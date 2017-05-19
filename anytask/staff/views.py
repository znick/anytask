# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.core.urlresolvers import reverse

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML

from courses.models import StudentCourseMark
from users.models import UserProfile
from users.model_user_profile_filter import UserProfileFilter
from users.model_user_status import UserStatus, get_statuses
from schools.models import School
from groups.models import Group

from django.contrib.auth.models import User, Permission, Group as Role
from guardian.decorators import permission_required_or_403
from guardian.shortcuts import get_objects_for_user
from guardian.utils import get_user_obj_perms_model
from permissions.decorators import any_obj_permission_required_or_403
from permissions.common import get_perm_local_name, get_superuser_perms, assign_perm_by_id, remove_perm_by_id
from permissions.models import PermissionsVisible, RolesVisible

from django.contrib.auth.decorators import user_passes_test

from collections import defaultdict

import csv
import logging
import json

logger = logging.getLogger('django.request')

MAX_FILE_SIZE = settings.FILE_UPLOAD_MAX_MEMORY_SIZE
SEARCH_FIELDS = {
    'login': 'user__username',
    'email': 'user__email',
}
TABLE_ROLES_OFFSET_COL = 2


@require_http_methods(['GET'])
@login_required
@permission_required_or_403('users.view_backoffice_page')
def staff_page(request):
    user = request.user

    context = {
        'user': user,
    }

    return render_to_response('staff.html', context, context_instance=RequestContext(request))


def get_perm_info(perm, roles, disabled=False):
    group_local_name, perm_local_name = get_perm_local_name(perm)
    perm_info = [
        {
            'id': perm.id,
            'name': perm_local_name
        },
        {
            'name': group_local_name
        }
    ]

    for role in roles:
        perm_info += [{
            'role_id': role.id,
            'is_checkbox': True,
            'disabled': disabled
        }]

    return perm_info


def get_perms_translated(perms, roles):
    perms_translated = {}
    for perm in perms:
        perms_translated[perm.id] = get_perm_info(perm, roles)

    return perms_translated


def get_roles_table_by_school(perms_translated, roles):
    header = []
    if roles:
        for role_i, role in enumerate(roles):
            header.append({
                'id': role.id,
                'name': role.name
            })
            for perm in role.permissions.all():
                if perm.id not in perms_translated:
                    perms_translated[perm.id] = get_perm_info(perm, roles, True)

                perms_translated[perm.id][role_i + TABLE_ROLES_OFFSET_COL].update({
                    'selected': True,
                })
    return {
        'header': header,
        'body': perms_translated,
    }


def get_perms_roles_visible(schools, perm_app_label=None, perm_codename=None, only_perms=False, only_roles=False):
    perms_visible = PermissionsVisible.objects.none()
    roles_visible = RolesVisible.objects.none()

    if not only_roles:
        perms_visible = PermissionsVisible.objects \
            .filter(
            school__in=schools,
            permission__content_type__app_label=perm_app_label,
            permission__codename=perm_codename
        ) \
            .distinct() \
            .prefetch_related('permissions') \
            .order_by('school__id')
    if not only_perms:
        roles_visible = RolesVisible.objects \
            .filter(school__in=schools) \
            .distinct() \
            .prefetch_related('roles', 'roles__permissions') \
            .order_by('school__id')

    return perms_visible, roles_visible


@require_http_methods(['GET'])
@login_required
def roles_page(request):
    user = request.user
    roles_tables = []

    if user.is_superuser:
        perms = get_superuser_perms()

        roles_global = Role.objects.filter(rolesvisible__isnull=True).prefetch_related("permissions")
        if roles_global:
            roles_tables.append({
                'school_info': {
                    'id': 0,
                    'name': _(u'obshchiye_roli')
                },
                'roles_info': get_roles_table_by_school(get_perms_translated(perms, roles_global), roles_global)
            })

        roles_visible = RolesVisible.objects \
            .all() \
            .prefetch_related('roles', 'roles__permissions', 'school') \
            .order_by('school__id')
        for role_visible in roles_visible:
            roles = role_visible.roles.all()
            roles_tables.append({
                'school_info': {
                    'id': role_visible.school.id,
                    'name': role_visible.school.name
                },
                'roles_info': get_roles_table_by_school(get_perms_translated(perms, roles), roles)
            })
    else:
        perm_app_label = 'schools'
        perm_codename = 'change_permissions'
        schools = get_objects_for_user(user, '.'.join([perm_app_label, perm_codename])).order_by('id')

        if not schools:
            raise PermissionDenied

        perms_visible, roles_visible = get_perms_roles_visible(schools, perm_app_label, perm_codename)

        perms_visible_i = 0
        roles_visible_i = 0
        for school in schools:
            perms = []
            if perms_visible_i < len(perms_visible) and perms_visible[perms_visible_i].school == school:
                perms = perms_visible[perms_visible_i].permissions.all()
                perms_visible_i += 1

            roles = []
            if roles_visible_i < len(roles_visible) and roles_visible[roles_visible_i].school == school:
                roles = roles_visible[roles_visible_i].roles.all()
                roles_visible_i += 1
            if perms or roles:
                roles_tables.append({
                    'school_info': {
                        'id': school.id,
                        'name': school.name
                    },
                    'roles_info': get_roles_table_by_school(get_perms_translated(perms, roles), roles)
                })

    context = {
        'user': user,
        'roles_tables': roles_tables,
    }
    return render_to_response('roles.html', context, context_instance=RequestContext(request))


def change_roles(changes_in_school, current_roles, perms):
    new_roles = []
    for role_id, role_changes in changes_in_school.iteritems():
        if role_id.startswith('new_'):
            role = Role.objects.create(name=role_changes.get('name'))
            new_roles.append(role)
        else:
            role = current_roles.filter(id=role_id)
            if len(role):
                role = role[0]
                if 'name' in role_changes:
                    role.name = role_changes['name']
                    role.save()

        if 'delete' in role_changes:
            role.delete()
            continue

        add_perms = perms & set(map(lambda x: int(x), role_changes.get('add', [])))
        remove_perms = perms & set(map(lambda x: int(x), role_changes.get('remove', [])))

        role.permissions = set(role.permissions.values_list("id", flat=True)) - remove_perms | add_perms

    return new_roles


@require_http_methods(['POST'])
@login_required
def ajax_change_roles(request):
    if not request.is_ajax():
        raise PermissionDenied
    if "changes" not in request.POST:
        raise PermissionDenied

    user = request.user
    changes = json.loads(request.POST.get("changes"))

    if user.is_superuser:
        perms = set(Permission.objects.all().values_list("id", flat=True))
        for school_id, roles_changes in changes.iteritems():
            roles_visible = RolesVisible.objects.none()
            if school_id == '0':
                current_roles = Role.objects.filter(rolesvisible__isnull=True).prefetch_related("permissions")
            else:
                roles_visible, created = RolesVisible.objects.get_or_create(school__id=school_id)
                current_roles = roles_visible.roles.all()
            new_roles = change_roles(roles_changes, current_roles, perms)
            if school_id != '0':
                roles_visible.roles.add(*new_roles)
    else:
        perm_app_label = 'schools'
        perm_codename = 'change_permissions'
        schools = get_objects_for_user(user, '.'.join([perm_app_label, perm_codename])) \
            .filter(id__in=changes.keys()) \
            .order_by('id')

        if not schools:
            raise PermissionDenied

        perms_visible, roles_visible = get_perms_roles_visible(schools, perm_app_label, perm_codename)

        perms_visible_i = 0
        roles_visible_i = 0
        for school in schools:
            perms = []
            if perms_visible_i < len(perms_visible) and perms_visible[perms_visible_i].school == school:
                perms = set(perms_visible[perms_visible_i].permissions.values_list("id", flat=True))
                perms_visible_i += 1

            current_roles = Role.objects.none()
            if roles_visible_i < len(roles_visible) and roles_visible[roles_visible_i].school == school:
                roles_visible_by_school = roles_visible[roles_visible_i]
                current_roles = roles_visible_by_school.roles.all()
                roles_visible_i += 1
            else:
                roles_visible_by_school = RolesVisible.objects.create(school=school)

            new_roles = change_roles(changes[str(school.id)], current_roles, perms)
            roles_visible_by_school.roles.add(*new_roles)

    return HttpResponse("OK")


def add_user_info(info, info_id, **kwargs):
    if info_id and info_id not in info:
        url_view = kwargs.pop("view", None)
        info[info_id] = dict(kwargs)
        if url_view:
            info[info_id]["url"] = reverse(url_view, args=[str(info_id)])
    return info


def get_users_info(users_raw, school_id=None):
    users_info = {}
    for user_info_raw in users_raw:
        if user_info_raw["id"] not in users_info:
            users_info[user_info_raw["id"]] = {
                "username": user_info_raw["username"],
                "last_name": user_info_raw["last_name"],
                "first_name": user_info_raw["first_name"],
                "url": reverse('users.views.users_redirect', args=[user_info_raw["username"]]),
                "courses_teacher": {},
                "courses": {},
                "groups": {},
                "roles": {},
            }
        users_info[user_info_raw["id"]]["courses_teacher"] = add_user_info(
            users_info[user_info_raw["id"]]["courses_teacher"],
            user_info_raw["course_teachers_set__id"],
            name=user_info_raw["course_teachers_set__name"],
            view='courses.views.course_page',
        )
        users_info[user_info_raw["id"]]["courses"] = add_user_info(
            users_info[user_info_raw["id"]]["courses"],
            user_info_raw["group__course__id"],
            name=user_info_raw["group__course__name"],
            view='courses.views.course_page',
        )
        users_info[user_info_raw["id"]]["groups"] = add_user_info(
            users_info[user_info_raw["id"]]["groups"],
            user_info_raw["group__id"],
            name=user_info_raw["group__name"]
        )
        if not school_id or user_info_raw["userroles__school__id"] == school_id:
            users_info[user_info_raw["id"]]["roles"] = add_user_info(
                users_info[user_info_raw["id"]]["roles"],
                user_info_raw["userroles__roles__id"],
                name=user_info_raw["userroles__roles__name"]
            )
    return users_info


def get_users_info_by_school(schools):
    users_tables = []
    for school in schools:
        users_info_raw = User.objects \
            .filter(Q(group__course__school=school) | Q(course_teachers_set__school=school)) \
            .distinct() \
            .values(
            "id",
            "username",
            "last_name",
            "first_name",
            "course_teachers_set__id",
            "course_teachers_set__name",
            "group__course__id",
            "group__course__name",
            "group__id",
            "group__name",
            "userroles__school__id",
            "userroles__roles__id",
            "userroles__roles__name",
        )


        users_tables.append({
            'school_info': {
                'id': school.id,
                'name': school.name
            },
            'users_info': get_users_info(users_info_raw, school.id),
        })

    return users_tables


@require_http_methods(['GET'])
@login_required
def roles_assign_page(request):
    user = request.user
    users_tables = []

    if user.is_superuser:
        schools = School.objects.all()
        users_info_raw = User.objects \
            .exclude(group__course__school__in=schools) \
            .exclude(course_teachers_set__school__in=schools) \
            .distinct() \
            .values(
            "id",
            "username",
            "last_name",
            "first_name",
            "course_teachers_set__id",
            "course_teachers_set__name",
            "group__course__id",
            "group__course__name",
            "group__id",
            "group__name",
            "userroles__roles__id",
            "userroles__roles__name",
        )

        users_tables.append({
            'school_info': {
                'id': 0,
                'name': _(u'bez_shkoly')
            },
            'users_info': get_users_info(users_info_raw)
        })

        users_tables += get_users_info_by_school(schools)
    else:
        perm_app_label = 'schools'
        perm_codename = 'change_permissions'
        schools = get_objects_for_user(user, '.'.join([perm_app_label, perm_codename])).order_by('id')

        if not schools:
            raise PermissionDenied

        users_tables = get_users_info_by_school(schools)

    context = {
        'user': user,
        'full_width_page': True,
        'users_tables': users_tables,
    }
    return render_to_response('roles_assign.html', context, context_instance=RequestContext(request))


def get_roles_perms(roles):
    roles_info = {}
    for role in roles:
        roles_info[role.id] = {
            'name': role.name,
            'perms': defaultdict(dict)
        }
        for perm in role.permissions.all():
            group_local_name, perm_local_name = get_perm_local_name(perm)
            roles_info[role.id]['perms'][perm.id] = {
                'model': perm.content_type.app_label,
                'codename': perm.codename,
                'name': perm_local_name,
                'model_name': group_local_name,
            }

    return roles_info


@require_http_methods(['GET'])
@login_required
def ajax_get_user_roles_info(request):
    if not request.is_ajax():
        raise PermissionDenied

    if "user_id" not in request.GET or "school_id" not in request.GET:
        raise PermissionDenied

    user = request.user
    response = {}
    school_id = int(request.GET["school_id"])

    if user.is_superuser:
        schools_qs = School.objects.all()
        try:
            user_to_change = User.objects.get(id=request.GET['user_id'])
        except User.DoesNotExist:
            raise PermissionDenied

        user_roles_qs = Role.objects.filter(userroles__user=user_to_change)
        if school_id != 0:
            user_roles_qs = user_roles_qs.filter(userroles__school__id=school_id)

            perms_visible, roles_visible = get_perms_roles_visible(
                [school_id],
                only_roles=True
            )
            roles = roles_visible[0].roles.all() if roles_visible else Role.objects.none()
        else:
            roles = Role.objects.all()

    else:
        perm_app_label = 'schools'
        perm_codename = 'change_permissions'
        schools_qs = School.objects.filter(id=school_id)

        if not schools_qs:
            raise PermissionDenied
        if not user.has_perm('.'.join([perm_app_label, perm_codename]), schools_qs[0]):
            raise PermissionDenied

        user_to_change = User.objects \
            .filter(Q(group__course__school=schools_qs[0]) | Q(course_teachers_set__school=schools_qs[0])) \
            .filter(id=request.GET['user_id']) \
            .distinct()
        if not user_to_change:
            raise PermissionDenied

        user_to_change = user_to_change[0]
        user_roles_qs = Role.objects.filter(userroles__user=user_to_change, userroles__school=schools_qs[0])

        perms_visible, roles_visible = get_perms_roles_visible(
            [schools_qs[0]],
            perm_app_label,
            perm_codename,
            only_roles=True
        )
        roles = roles_visible[0].roles.all() if roles_visible else Role.objects.none()

    user_roles = {}
    for user_role in user_roles_qs:
        user_roles[user_role.id] = {
            'name': user_role.name,
            'perms': user_to_change.get_profile().get_perms_by_role(user_role)
        }

    schools = {}
    courses = {}
    groups = {}
    for info_raw in schools_qs.values(
            "id",
            "name",
            "courses__id",
            "courses__is_active",
            "courses__name",
            "courses__groups__id",
            "courses__groups__name",
    ):
        if info_raw["id"]:
            schools[info_raw["id"]] = info_raw["name"]
        if info_raw["courses__id"]:
            courses[info_raw["courses__id"]] = info_raw["courses__name"]
        if info_raw["courses__groups__id"]:
            groups[info_raw["courses__groups__id"]] = info_raw["courses__groups__name"]

            # if info_raw["id"] not in courses:
            #     courses[info_raw["id"]] = {
            #         "name": info_raw["name"],
            #         "values": {},
            #     }
            # courses[info_raw["id"]]["values"][info_raw["courses__id"]] = info_raw["courses__name"]
            #
            # if info_raw["courses__id"] not in groups:
            #     groups[info_raw["courses__id"]] = {
            #         "name": info_raw["courses__name"],
            #         "values": {},
            #     }
            # groups[info_raw["courses__id"]]["values"][info_raw["courses__groups__id"]] = \
            #     info_raw["courses__groups__name"]

    response["schools"] = schools
    response["courses"] = courses
    response["groups"] = groups
    response["type_trans"] = {
        "schools" : _(u'shkoly'),
        "courses" : _(u'kursy'),
        "groups" : _(u'gruppy'),
    }
    response["user_roles"] = user_roles
    response["roles"] = get_roles_perms(roles.exclude(id__in=user_roles.keys()))

    return HttpResponse(json.dumps(response), content_type="application/json")


def get_roles_by_id(role_ids, school, is_superuser):
    if is_superuser:
        roles = Role.objects.filter(id__in=role_ids)
    else:
        roles = Role.objects.filter(id__in=role_ids, rolesvisible__school=school)

    if not roles:
        raise PermissionDenied

    return roles


@require_http_methods(['POST'])
@login_required
def ajax_save_user_roles(request):
    if not request.is_ajax():
        raise PermissionDenied

    for key in ["user_id", "school_id"]:
        if key not in request.POST:
            raise PermissionDenied

    user = request.user
    school_id = int(request.POST['school_id'])
    school = None
    if school_id != 0:
        try:
            school = School.objects.get(id=school_id)
        except School.DoesNotExist:
            raise PermissionDenied

    if user.is_superuser:
        try:
            user_to_change = User.objects \
                .distinct() \
                .get(id=request.POST['user_id'])
        except User.DoesNotExist:
            raise PermissionDenied
    else:
        if not user.has_perm("schools.change_permissions", school):
            raise PermissionDenied

        try:
            user_to_change = User.objects \
                .filter(Q(group__course__school=school) | Q(course_teachers_set__school=school)) \
                .distinct() \
                .get(id=request.POST['user_id'])
        except User.DoesNotExist:
            raise PermissionDenied

    user_to_change_profile = user_to_change.get_profile()
    if "role_id" in request.POST and 'new_role_perms' in request.POST:
        role = get_roles_by_id([request.POST['role_id']], school, user.is_superuser)
        user_to_change_profile.add_role(role[0], json.loads(request.POST['new_role_perms']), school)

    if "deleted_roles[]" in request.POST and 'new_role_perms' in request.POST:
        deleted_roles = get_roles_by_id(request.POST.getlist("deleted_roles[]"), school, user.is_superuser)
        for role in deleted_roles:
            user_to_change_profile.remove_role(role, school)

    if "user_roles_changes" in request.POST:
        for role_id, role_changes in json.loads(request.POST["user_roles_changes"]).iteritems():
            for perm_id, perm_info in role_changes.iteritems():
                try:
                    perm = Permission.objects.get(id=perm_id)
                except Permission.DoesNotExist:
                    raise PermissionDenied

                model = perm.content_type.model_class()
                try:
                    for obj in model.objects.filter(id__in=perm_info.get("add", [])):
                        assign_perm_by_id(perm, user_to_change, obj, role_id)
                except Exception as e:
                    print e
                for obj in model.objects.filter(id__in=perm_info.get("remove", [])):
                    remove_perm_by_id(perm, user_to_change, obj, role_id)

    return HttpResponse("OK")


@require_http_methods(['GET', 'POST'])
@login_required
@any_obj_permission_required_or_403('schools.view_users_status_filter')
def user_filter_by_status_page(request):
    user = request.user

    user_profiles = None
    file_filter_err = ''
    is_error = False
    show_file_alert = False
    empty_filter = False
    if request.method == 'POST':
        show_file_alert = True
        if 'file_input' not in request.FILES:
            raise PermissionDenied

        file_filter = request.FILES['file_input']
        if file_filter.size > MAX_FILE_SIZE:
            file_filter.close()
            raise PermissionDenied

        reader = csv.reader(file_filter, delimiter=";")

        try:
            fieldnames = reader.next()

            if len(fieldnames) == 1 and fieldnames[0] in SEARCH_FIELDS:
                search_values = set(row[0] for row in reader)
                user_profiles = UserProfile.objects.filter(
                    **{SEARCH_FIELDS[fieldnames[0]] + '__in': list(search_values)})
                if len(user_profiles) != len(search_values):
                    err_search_values = search_values - set(
                        user_profiles.values_list(SEARCH_FIELDS[fieldnames[0]], flat=True))
                    file_filter_err = u'<strong>{0}</strong><br/>'.format(_(u'dannyye_polzovateli_ne_naydeny')) + \
                                      u', '.join(err_search_values)
            else:
                file_filter_err = _(u'nevernyy_format_fayla')
                is_error = True
        except Exception as e:
            logger.error('Error in staff page file filter upload: %s', e)
            file_filter_err = str(e)
            is_error = True
    elif request.method == 'GET' and not request.GET:
        user_profiles = UserProfile.objects.none()
        empty_filter = True

    f = UserProfileFilter(request.GET if request.method == 'GET' else {}, queryset=user_profiles)
    f.set()

    f.form.helper = FormHelper(f.form)
    f.form.helper.form_method = 'get'
    f.form.helper.layout.append(HTML(u"""<div class="form-group row">
        <button id="button_filter" class="btn btn-secondary pull-xs-right" type="submit">{0}</button>
</div>""".format(_(u'primenit'))))

    context = {
        'filter': f,
        'file_filter_err': file_filter_err,
        'is_error': is_error,
        'statuses': get_statuses(),
        'show_file_alert': show_file_alert,
        'empty_filter': empty_filter,
    }

    return render_to_response('user_filter_by_status.html', context, context_instance=RequestContext(request))


@require_http_methods(['POST'])
@login_required
def ajax_change_status(request):
    if not request.is_ajax():
        raise PermissionDenied

    post_dict = dict(request.POST)
    if 'statuses_id[]' in post_dict and 'profile_ids[]' in post_dict:
        statuses = UserStatus.objects.filter(id__in=post_dict['statuses_id[]'])
        for profile in UserProfile.objects.filter(id__in=post_dict['profile_ids[]']):
            for status in statuses:
                profile.set_status(status)

    return HttpResponse("OK")


@require_http_methods(['POST'])
@login_required
def ajax_save_ids(request):
    if not request.is_ajax():
        raise PermissionDenied

    post_dict = dict(request.POST)
    if 'user_ids[]' in post_dict:
        index = save_to_session(request, post_dict['user_ids[]'])
    else:
        raise PermissionDenied

    return HttpResponse(json.dumps({'index': index}), content_type="application/json")


def save_to_session(request, user_ids):
    index = request.session.get('user_ids_send_mail_counter', -1) + 1
    request.session['user_ids_send_mail_counter'] = index
    request.session['user_ids_send_mail_' + str(index)] = user_ids

    return index


@require_http_methods(['GET'])
@login_required
@any_obj_permission_required_or_403('schools.view_users_status_filter')
def get_gradebook(request):
    user = request.user

    statuses = UserStatus.objects.filter(type='activity')

    context = {
        'statuses': statuses,
    }

    return render_to_response('get_gradebook.html', context, context_instance=RequestContext(request))


@require_http_methods(['GET'])
@login_required
@any_obj_permission_required_or_403('schools.view_users_status_filter')
def gradebook_page(request, statuses=None):
    user = request.user

    user_statuses = []
    for status_id in statuses.split('_'):
        if status_id:
            user_statuses.append(get_object_or_404(UserStatus, id=int(status_id)))
    students = set()
    profiles = UserProfile.objects.filter(user_status__in=user_statuses).all()
    for profile in profiles:
        students.add(profile.user)

    marks = StudentCourseMark.objects.filter(student__in=students).order_by('course')

    courses = set()
    for mark in marks:
        courses.add(mark.course)

    students_with_marks = []
    for student in students:
        entry = {}
        marks_for_student = []
        entry['name'] = student.get_full_name()
        entry['url'] = student.get_absolute_url()
        for course in courses:
            if marks.filter(student=student, course=course):
                mark = marks.get(student=student, course=course).mark
            else:
                mark = None
            marks_for_student.append(mark if mark else '--')
        entry['marks'] = marks_for_student
        students_with_marks.append(entry)

    context = {
        'students': students_with_marks,
        'courses': courses,
    }

    return render_to_response('gradebook.html', context, context_instance=RequestContext(request))
