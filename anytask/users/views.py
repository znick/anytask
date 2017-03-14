# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Q
from django.db.models import Sum
from django.conf import settings
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.utils.translation import ugettext as _


from users.models import UserProfile, UserProfileLog
from users.model_user_status import UserStatus
from issues.model_issue_student_filter import IssueFilterStudent
from django.contrib.auth.models import User
from tasks.models import TaskTaken
from years.models import Year
from groups.models import Group
from courses.models import Course, StudentCourseMark
from invites.models import Invite
from issues.models import Issue
from tasks.models import Task
from schools.models import School
from users.forms import InviteActivationForm

from years.common import get_current_year

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML

import yandex_oauth
import requests
import json


@login_required
def users_redirect(request, username):
    return redirect('users.views.profile', username=username, permanent=True)


@login_required
def profile(request, username=None, year=None):
    user = request.user

    user_to_show = user
    if username:
        user_to_show = get_object_or_404(User, username=username)

    show_email = True
    user_above_user_to_show = True

    if user_to_show != user:
        user_teach_user_to_show = False
        user_to_show_teach_user = False
        user_school_user_to_show = False
        user_school_teach_user_to_show = False

        groups_user_to_show = user_to_show.group_set.all()
        groups = user.group_set.all()

        courses_user_to_show = Course.objects.filter(groups__in=groups_user_to_show)
        schools_user_to_show = School.objects.filter(courses__in=courses_user_to_show)
        courses_user_to_show_teacher = Course.objects.filter(teachers=user_to_show)
        schools_user_to_show_teacher = School.objects.filter(courses__in=courses_user_to_show_teacher)

        courses = Course.objects.filter(groups__in=groups)
        schools = School.objects.filter(courses__in=courses)
        courses_teacher = Course.objects.filter(teachers=user)
        schools_teacher = School.objects.filter(courses__in=courses_teacher)

        if courses_user_to_show_teacher & courses:
            user_to_show_teach_user = True

        if courses_teacher & courses_user_to_show:
            user_teach_user_to_show = True

        if (schools_user_to_show | schools_user_to_show_teacher) & (schools | schools_teacher):
            user_school_user_to_show = True

        if schools_teacher & schools_user_to_show:
            user_school_teach_user_to_show = True

        if not (user.is_staff or user_school_user_to_show):
            if not ((courses_user_to_show | courses_user_to_show_teacher) & (courses | courses_teacher)):
                if not (groups_user_to_show & groups):
                    raise PermissionDenied

        show_email = user.is_staff or \
                     user_to_show.get_profile().show_email or \
                     user_teach_user_to_show or \
                     user_to_show_teach_user
        user_above_user_to_show = user.is_staff or \
                                  user_school_teach_user_to_show

    teacher_in_courses = Course.objects.filter(is_active=True).filter(teachers=user_to_show).distinct()

    if year:
        current_year = get_object_or_404(Year, start_year=year)
    else:
        current_year = get_current_year()

    groups = user_to_show.group_set.all().distinct()

    courses = Course.objects.filter(is_active=True).filter(groups__in=groups).distinct()

    can_sync_contest = False
    for course in Course.objects.filter(is_active=True):
        if course.get_user_group(user) and course.send_to_contest_from_users:
            can_sync_contest = True

    can_generate_invites = user_to_show == user and Invite.user_can_generate_invite(user)



    invite_form = InviteActivationForm()

    if request.method == 'POST':
        user_profile = user.get_profile()
        if 'update-avatar' in request.POST:
            filename = 'avatar'
            if 'input-avatar' in request.FILES:
                image_content = request.FILES['input-avatar']
                user_profile.avatar.save(filename, image_content)
            elif request.POST['gravatar-link']:
                image_content = ContentFile(requests.get(request.POST['gravatar-link']).content)
                user_profile.avatar.save(filename, image_content)

            user_profile.save()
        else:
            invite_form = InviteActivationForm(request.POST)
            if invite_form.is_valid():
                invite = get_object_or_404(Invite, key=invite_form.cleaned_data['invite'])
                if invite.group:
                    invite.group.students.add(user)
                    invite.invited_users.add(user)

    teacher_in_courses_archive = Course.objects.filter(is_active=False).filter(teachers=user_to_show).distinct()
    courses_archive = Course.objects.filter(is_active=False).filter(groups__in=groups).distinct()

    card_width = ''
    if len(teacher_in_courses or teacher_in_courses_archive) != 0 and \
       len(courses or courses_archive) != 0 and \
       len(groups) != 0:
        card_width = 'col-md-4'
    elif len(teacher_in_courses or teacher_in_courses_archive) != 0 and len(courses or courses_archive) != 0 or \
         len(teacher_in_courses or teacher_in_courses_archive) != 0 and len(groups) != 0 or \
         len(courses or courses_archive) != 0 and len(groups) != 0:
        card_width = 'col-md-6'
    else:
        card_width = 'col-md-12'

    context = {
        'user_to_show'              : user_to_show,
        'courses'                   : group_by_year(courses),
        'courses_archive'           : group_by_year(courses_archive),
        'groups'                    : group_by_year(groups),
        # 'user_course_information'   : user_course_information,
        'teacher_in_courses'        : group_by_year(teacher_in_courses),
        'teacher_in_courses_archive': group_by_year(teacher_in_courses_archive),
        'current_year'              : unicode(current_year) if current_year is not None else '',
        'can_generate_invites'      : can_generate_invites,
        'invite_form'               : invite_form,
        'user_to_show_profile'      : user_to_show.get_profile(),
        'card_width'                : card_width,
        'show_email'                : show_email,
        'user_above_user_to_show'   : user_above_user_to_show,
    }

    return render_to_response('user_profile.html', context, context_instance=RequestContext(request))


def group_by_year(objects):
    group_dict = {}
    for obj in objects:
        year = unicode(obj.year)
        if year in group_dict:
            group_dict[year].append(obj)
        else:
            group_dict[year] = [obj]

    return sorted(group_dict.iteritems())

@login_required
def profile_settings(request):
    user = request.user

    user_profile = user.get_profile()

    if request.method == 'POST':
        user_profile.show_email = True if 'show_email' in request.POST else False
        user_profile.send_my_own_events = True if 'send_my_own_events' in request.POST else False
        user_profile.save()

        return HttpResponse("OK")

    context = {
        'user_profile': user_profile,
    }

    return render_to_response('user_settings.html', context, context_instance=RequestContext(request))


@login_required
def profile_history(request, username=None):
    if request.method == 'POST':
        return HttpResponseForbidden()

    user = request.user

    if not user.is_staff:
        raise PermissionDenied

    user_to_show = user
    if username:
        user_to_show = get_object_or_404(User, username=username)

    context = {
        'user_profile':         user_to_show.get_profile(),
        'user_profile_history': UserProfileLog.objects.filter(user=user_to_show).order_by('update_time'),
        'user_to_show':         user_to_show,
        'status_types':         UserStatus.TYPE_STATUSES,
        'user_statuses':        UserStatus.objects.all(),
    }

    return render_to_response('status_history.html', context, context_instance=RequestContext(request))


@login_required
def set_user_statuses(request, username=None):
    if request.method == 'GET':
        return HttpResponseForbidden()

    user = request.user

    if not user.is_staff:
        return HttpResponseForbidden()

    user_to_show = user
    if username:
        user_to_show = get_object_or_404(User, username=username)

    user_profile = user_to_show.get_profile()
    is_error = False
    error = ''
    user_statuses = []

    try:
        new_user_statuses = dict(request.POST)['status_by_type[]']
        if not new_user_statuses:
            new_user_statuses = []
        old_user_statuses = user_profile.user_status.all()

        for status in old_user_statuses:
            if str(status.id) not in new_user_statuses:
                user_profile.user_status.remove(status)

        for status_id in new_user_statuses:
            if status_id:
                status = UserStatus.objects.get(id=status_id)
                if status not in user_profile.user_status.all():
                    user_profile.user_status.add(status)

        user_profile.updated_by = user
        user_profile.save()

    except Exception as e:
        is_error = True
        error = e

    for status in user_profile.user_status.all():
        user_statuses.append({'name': status.name, 'color': status.color})

    user_profile_log = {'update_time': user_profile.update_time.strftime("%d-%m-%Y %H:%M"),
                        'updated_by': user_profile.updated_by.username,
                        'fullname': user_profile.updated_by.get_full_name(),}

    return HttpResponse(json.dumps({'user_statuses': user_statuses,
                                    'user_profile_log' : user_profile_log,
                                    'is_error': is_error,
                                    'error': error}),
                        content_type="application/json")


@login_required
def ya_oauth_request(request, type_of_oauth):
    if type_of_oauth == 'contest':
        OAUTH = settings.CONTEST_OAUTH_ID
        PASSWORD = settings.CONTEST_OAUTH_PASSWORD
    elif type_of_oauth == 'passport':
        OAUTH = settings.PASSPORT_OAUTH_ID
        PASSWORD = settings.PASSPORT_OAUTH_PASSWORD

    ya_oauth = yandex_oauth.OAuthYandex(OAUTH,PASSWORD)

    return redirect(ya_oauth.get_code())


def ya_oauth_contest(user, ya_response, ya_contest_response):
    user_profile = user.get_profile()
    if not user_profile.ya_contest_oauth:
        users_with_ya_contest_oauth = UserProfile.objects.all().filter(~Q(ya_contest_login=''))

        for user in users_with_ya_contest_oauth:
            if user.ya_contest_login == ya_contest_response['login'] or user.ya_contest_uid == \
                    ya_contest_response['id']:
                return redirect('users.views.ya_oauth_forbidden', type_of_oauth='contest')

    if not user_profile.ya_contest_oauth or user_profile.ya_contest_login == ya_contest_response['login']:
        user_profile.ya_contest_oauth = ya_response['access_token']
        user_profile.ya_contest_uid = ya_contest_response['id']
        user_profile.ya_contest_login = ya_contest_response['login']
        user_profile.save()
    else:
        return redirect('users.views.ya_oauth_changed')

    return redirect('users.views.profile_settings')


def ya_oauth_passport(user, ya_response, ya_passport_response):
    user_profile = user.get_profile()

    if not user_profile.ya_passport_oauth:
        for user_p in UserProfile.objects.exclude(ya_passport_email=''):
            if user_p.ya_passport_uid == ya_passport_response['id'] or \
                            user_p.ya_passport_login == ya_passport_response['login'] or \
                            user_p.ya_passport_email == ya_passport_response['default_email']:
                return redirect('users.views.ya_oauth_forbidden', type_of_oauth='passport')

    user_profile.ya_passport_oauth = ya_response['access_token']
    user_profile.ya_passport_uid = ya_passport_response['id']
    user_profile.ya_passport_login = ya_passport_response['login']
    user_profile.ya_passport_email = ya_passport_response['default_email']
    user_profile.save()

    return redirect('users.views.profile_settings')


@login_required
def ya_oauth_response(request, type_of_oauth):
    if request.method != 'GET':
        return HttpResponseForbidden()

    user = request.user
    OAUTH = ''
    PASSWORD = ''

    if type_of_oauth == 'contest':
        OAUTH = settings.CONTEST_OAUTH_ID
        PASSWORD = settings.CONTEST_OAUTH_PASSWORD
    elif type_of_oauth == 'passport':
        OAUTH = settings.PASSPORT_OAUTH_ID
        PASSWORD = settings.PASSPORT_OAUTH_PASSWORD

    ya_oauth = yandex_oauth.OAuthYandex(OAUTH, PASSWORD)
    ya_response = ya_oauth.get_token(int(request.GET['code']))
    ya_passport_response = requests.get('https://login.yandex.ru/info?json&oauth_token=' + ya_response['access_token'])

    request.session["ya_oauth_login"] = ya_passport_response.json()['login']

    if type_of_oauth == 'contest':
        return ya_oauth_contest(user, ya_response, ya_passport_response.json())
    elif type_of_oauth == 'passport':
        return ya_oauth_passport(user, ya_response, ya_passport_response.json())

    return HttpResponseForbidden()


@login_required
def ya_oauth_disable(request, type_of_oauth):
    user = request.user
    user_profile = user.get_profile()
    if type_of_oauth == 'contest':
        pass
    elif type_of_oauth == 'passport':
        user_profile.ya_passport_oauth = ""
        user_profile.ya_passport_uid = None
        user_profile.ya_passport_login = ""
        user_profile.ya_passport_email = ""

    user_profile.save()

    return redirect('users.views.profile_settings')


@login_required
def ya_oauth_forbidden(request, type_of_oauth):
    oauth_error_text_header = ''
    oauth_error_text = _(u"Профиль {0} уже привязан к аккаунту другого пользователя на Anytask!")\
        .format(request.session["ya_oauth_login"])
    if type_of_oauth == 'contest':
        oauth_error_text_header = _(u"Привязать профиль Яндекс.Контеста")
    elif type_of_oauth == 'passport':
        oauth_error_text_header = _(u"Привязать профиль Яндекса")
    context = {
        'oauth_error_text_header' : oauth_error_text_header,
        'oauth_error_text'        : oauth_error_text,
    }

    return render_to_response('oauth_error.html', context, context_instance=RequestContext(request))


@login_required
def ya_oauth_changed(request):
    context = {
        'oauth_error_text_header':  _(u"Привязать профиль Яндекс.Контеста"),
        'oauth_error_text'       : _(u"Можно перепривязать только тот профиль, который был привязан ранее!"),
    }

    return render_to_response('oauth_error.html', context, context_instance=RequestContext(request))


def add_user_to_group(request):
    user = request.user

    if not request.method == 'POST':
        return HttpResponseForbidden()

    if 'group_id' not in request.POST:
        return HttpResponseForbidden()

    try:
        group_id = int(request.POST['group_id'])
    except ValueError:
        return HttpResponseForbidden()

    group = get_object_or_404(Group, id=group_id)
    group.students.add(user)
    group.save()

    return HttpResponse("OK")


@login_required
def my_tasks(request):
    user = request.user
    issues = Issue.objects.filter(student=user).order_by('-update_time')

    user_as_str = str(user.username) + '_tasks_filter'

    f = IssueFilterStudent(request.GET, issues)
    f.set_user(user)

    if f.form.data:
        request.session[user_as_str] = f.form.data
    elif user_as_str in request.session:
        f.form.data = request.session.get(user_as_str)

    f.form.helper = FormHelper(f.form)
    f.form.helper.form_method = 'get'
    f.form.helper.layout.append(HTML(u"""<div class="form-group row">
                                           <button id="button_filter" class="btn btn-secondary pull-xs-right" type="submit">{0}</button>
                                         </div>""".format(_(u'Применить'))))

    context = {
        'filter': f,
    }

    return render_to_response('my_tasks.html', context, context_instance=RequestContext(request))


@login_required
def user_courses(request, username=None, year=None):
    user = request.user

    user_to_show = user
    if username:
        user_to_show = get_object_or_404(User, username=username)

    if user_to_show != user:
        user_school_teach_user_to_show = False

        groups_user_to_show = user_to_show.group_set.all()

        courses_user_to_show = Course.objects.filter(groups__in=groups_user_to_show)
        schools_user_to_show = School.objects.filter(courses__in=courses_user_to_show)

        courses_teacher = Course.objects.filter(teachers=user)
        schools_teacher = School.objects.filter(courses__in=courses_teacher)

        if schools_teacher & schools_user_to_show:
            user_school_teach_user_to_show = True

        if not (user.is_staff or user_school_teach_user_to_show):
            raise PermissionDenied

    if year:
        current_year = get_object_or_404(Year, start_year=year)
    else:
        current_year = get_current_year()

    groups = user_to_show.group_set.all()

    courses = Course.objects.filter(groups__in=groups).distinct()

    tables = [{}, {}]

    for course in courses:

        tasks = Task.objects.filter(course=course, groups__in=groups, is_hidden=False).distinct()
        issues = Issue.objects.filter(student=user_to_show).filter(task__in=tasks)

        if StudentCourseMark.objects.filter(student=user_to_show, course=course):
            mark = StudentCourseMark.objects.get(student=user_to_show, course=course).mark
        else:
            mark = None

        student_summ_score = issues.aggregate(Sum('mark'))['mark__sum'] or 0

        new_course_statistics = dict()
        new_course_statistics['name'] = course.name
        new_course_statistics['url'] = course.get_absolute_url()

        new_course_statistics['issues_count'] = []
        for status in course.issue_status_system.statuses.all():
            new_course_statistics['issues_count'].append((status, issues.filter(status_field=status).count()))

        new_course_statistics['tasks'] = tasks.count
        new_course_statistics['mark'] = mark if mark else '--'
        new_course_statistics['summ_score'] = student_summ_score

        is_archive = int(not course.is_active)
        table_year = unicode(course.year)
        table_key = course.issue_status_system.id

        if table_year not in tables[is_archive]:
            tables[is_archive][table_year] = dict()

        if table_key in tables[is_archive][table_year]:
            tables[is_archive][table_year][table_key].append(new_course_statistics)
        else:
            tables[is_archive][table_year][table_key] = [new_course_statistics]

    context = {
        'tables'            : [sorted(x.iteritems()) for x in tables],
        'current_year'      : unicode(current_year) if current_year is not None else '',
        'user_to_show'      : user_to_show,
        'user'              : user,
    }

    return render_to_response('user_courses.html', context, context_instance=RequestContext(request))


@login_required
def activate_invite(request):
    user = request.user
    if request.method != 'POST':
        return HttpResponseForbidden()

    invite_form = InviteActivationForm(request.POST)
    if invite_form.is_valid():
        invite = get_object_or_404(Invite, key=invite_form.cleaned_data['invite'])
        if 'course_id' in request.POST:
            course = get_object_or_404(Course, id=int(request.POST['course_id']))
            if invite.group and invite.group in course.groups.all():
                invite.group.students.add(user)
                invite.invited_users.add(user)
            else:
                return HttpResponse(json.dumps({'is_error': True,
                                                'invite': _(u'Инвайт относится к другому курсу.')}),
                                    content_type="application/json")

        elif invite.group:
            invite.group.students.add(user)
            invite.invited_users.add(user)
    else:
        data = dict(invite_form.errors)
        data['is_error'] = True
        return HttpResponse(json.dumps(data),
                            content_type="application/json")

    return HttpResponse(json.dumps({"is_error": False}),
                        content_type="application/json")


@login_required
def ajax_edit_user_info(request):
    if not request.method == 'POST' and not request.is_ajax():
        return HttpResponseForbidden()

    user = request.user
    user_profile = user.get_profile()

    user_info = ''
    if 'user-info' in request.POST:
        user_info = request.POST['user-info'].strip()

    if user_info and not user_info.startswith(u'<div class="not-sanitize">'):
        user_info = u'<div class="not-sanitize">' + user_info + u'</div>'

    user_profile.info = user_info
    user_profile.save()

    return HttpResponse(json.dumps({'info': user_info}),
                        content_type="application/json")
