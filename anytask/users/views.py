# -*- coding: utf-8 -*-

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.db.models import Q
from django.db.models import Sum
from django.conf import settings
from django.utils.http import is_safe_url
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from django.utils.translation import check_for_language
from django.utils import timezone

from users.models import UserProfile
from users.model_user_status import UserStatus
from issues.model_issue_student_filter import IssueFilterStudent
from django.contrib.auth.models import User
from years.models import Year
from groups.models import Group
from courses.models import Course, StudentCourseMark
from invites.models import Invite
from issues.models import Issue
from issues.model_issue_status import IssueStatus
from tasks.models import Task
from schools.models import School
from users.forms import InviteActivationForm
from anytask.common.timezone import get_tz
from pytz import timezone as timezone_pytz

from years.common import get_current_year

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from dateutil.relativedelta import relativedelta
from urllib.parse import urlparse

import yandex_oauth
import requests
import json
import datetime
import pytz
from reversion import revisions as reversion


@login_required
def users_redirect(request, username):
    return redirect('users.views.profile', username=username, permanent=True)


@login_required
def profile(request, username=None, year=None):
    user = request.user

    user_to_show = user
    if username:
        user_to_show = get_object_or_404(User, username=username)

    user_to_show_profile = user_to_show.profile

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

        show_email = \
            user.is_staff or \
            user_to_show_profile.show_email or \
            user_teach_user_to_show or \
            user_to_show_teach_user
        user_above_user_to_show = \
            user.is_staff or \
            user_school_teach_user_to_show

    teacher_in_courses = Course.objects.filter(is_active=True).filter(teachers=user_to_show).distinct()

    if year:
        current_year = get_object_or_404(Year, start_year=year)
    else:
        current_year = get_current_year()

    groups = user_to_show.group_set.all().distinct()

    courses = Course.objects.filter(is_active=True).filter(groups__in=groups).distinct()

    can_generate_invites = user_to_show == user and Invite.user_can_generate_invite(user)

    invite_form = InviteActivationForm()

    if request.method == 'POST':
        user_profile = user.profile
        if 'update-avatar' in request.POST:
            filename = 'avatar'
            if 'input-avatar' in request.FILES:
                image_content = request.FILES['input-avatar']
                user_profile.avatar.save(filename, image_content)
            elif request.POST['delete-avatar']:
                user_profile.avatar.delete()
            # elif request.POST['gravatar-link']:
            #     image_content = ContentFile(requests.get(request.POST['gravatar-link']).content)
            #     user_profile.avatar.save(filename, image_content)

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

    if len(teacher_in_courses or teacher_in_courses_archive) != 0 \
            and len(courses or courses_archive) != 0 \
            and len(groups) != 0:
        card_width = 'col-md-4'
    elif len(teacher_in_courses or teacher_in_courses_archive) != 0 \
            and len(courses or courses_archive) != 0 or len(teacher_in_courses or teacher_in_courses_archive) != 0 \
            and len(groups) != 0 or len(courses or courses_archive) != 0 \
            and len(groups) != 0:
        card_width = 'col-md-6'
    else:
        card_width = 'col-md-12'

    age = 0
    if user.is_staff and user_to_show_profile.birth_date:
        age = relativedelta(datetime.datetime.now(), user_to_show_profile.birth_date).years
        age = age if age > 0 else 0

    context = {
        'user_to_show': user_to_show,
        'courses': group_by_year(courses),
        'courses_archive': group_by_year(courses_archive),
        'groups': group_by_year(groups),
        'teacher_in_courses': group_by_year(teacher_in_courses),
        'teacher_in_courses_archive': group_by_year(teacher_in_courses_archive),
        'current_year': str(current_year) if current_year is not None else '',
        'can_generate_invites': can_generate_invites,
        'invite_form': invite_form,
        'user_to_show_profile': user_to_show_profile,
        'card_width': card_width,
        'show_email': show_email,
        'user_above_user_to_show': user_above_user_to_show,
        'age': age,
    }

    return render(request, 'user_profile.html', context)


def group_by_year(objects):
    group_dict = {}
    for obj in objects:
        year = str(obj.year)
        if year in group_dict:
            group_dict[year].append(obj)
        else:
            group_dict[year] = [obj]

    return sorted(group_dict.items())


@login_required
def profile_settings(request):
    user = request.user
    user_profile = user.profile

    if request.method == 'POST':
        user_profile.show_email = 'show_email' in request.POST
        user_profile.send_my_own_events = 'send_my_own_events' in request.POST
        user_profile.location = request.POST.get('location', '')
        if 'geoid' in request.POST:
            tz = get_tz(request.POST['geoid'])
            user_profile.time_zone = tz
            request.session['django_timezone'] = tz
            timezone.activate(pytz.timezone(tz))
        user_profile.save()

        return HttpResponse("OK")

    context = {
        'user_profile': user_profile,
        'geo_suggest_url': settings.GEO_SUGGEST_URL
    }

    return render(request, 'user_settings.html', context)


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
    user_profile = user_to_show.profile

    version_list = reversion.get_for_object(user_profile)
    user_status_prev = None
    history = []
    for version in reversed(version_list):
        user_status_cur = set(version.field_dict['user_status'])
        if user_status_cur == user_status_prev:
            continue
        history.append({
            'update_time': version.revision.date_created,
            'updated_by': version.revision.user,
            'user_statuses': UserStatus.objects.filter(id__in=user_status_cur).order_by("type").values("color", "name")
        })

        user_status_prev = user_status_cur

    context = {
        'user_profile': user_profile,
        'user_profile_history': history,
        'user_to_show': user_to_show,
        'status_types': UserStatus.TYPE_STATUSES,
        'user_statuses': UserStatus.objects.all(),
    }

    return render(request, 'status_history.html', context)


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

    user_profile = user_to_show.profile
    is_error = False
    error = ''

    try:
        user_profile.user_status = filter(bool, dict(request.POST).get('status_by_type[]', []))
        user_profile.updated_by = user
        user_profile.save()
        reversion.set_user(user)
        reversion.set_comment("Change from user profile")
    except Exception as e:
        is_error = True
        error = str(e)

    user_statuses = list(user_profile.user_status.all().values("name", "color"))

    user_profile_log = {
        'update_time': user_profile.update_time.astimezone(
            timezone_pytz(user.profile.time_zone)
        ).strftime("%d-%m-%Y %H:%M"),
        'updated_by': user_profile.updated_by.username,
        'fullname': user_profile.updated_by.get_full_name()
    }

    return HttpResponse(json.dumps({'user_statuses': user_statuses,
                                    'user_profile_log': user_profile_log,
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

    ya_oauth = yandex_oauth.OAuthYandex(OAUTH, PASSWORD)

    return redirect(ya_oauth.get_code())


def ya_oauth_contest(user, ya_response, ya_contest_response):
    user_profile = user.profile
    if not user_profile.ya_contest_oauth:
        users_with_ya_contest_oauth = UserProfile.objects.filter(
            Q(ya_contest_login=ya_contest_response['login']) | Q(ya_contest_uid=ya_contest_response['id'])
        ).exclude(
            ya_contest_login=user_profile.ya_contest_login
        )
        if users_with_ya_contest_oauth:
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
    user_profile = user.profile

    if not user_profile.ya_passport_oauth:
        for user_p in UserProfile.objects.exclude(ya_passport_email=''):
            if user_p.ya_passport_uid == ya_passport_response['id'] \
                    or user_p.ya_passport_login == ya_passport_response['login'] \
                    or user_p.ya_passport_email == ya_passport_response['default_email']:
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
    if request.method == "GET":
        user_profile = user.profile
        response = redirect('users.views.profile_settings')
    elif user.is_superuser and request.method == "POST" and "profile_id" in request.POST:
        user_profile = get_object_or_404(UserProfile, id=request.POST["profile_id"])
        response = HttpResponse("OK")
    else:
        raise PermissionDenied

    if type_of_oauth == 'contest':
        if user.is_superuser:
            user_profile.ya_contest_oauth = ""
            user_profile.ya_contest_uid = None
            user_profile.ya_contest_login = ""
    elif type_of_oauth == 'passport':
        user_profile.ya_passport_oauth = ""
        user_profile.ya_passport_uid = None
        user_profile.ya_passport_login = ""
        user_profile.ya_passport_email = ""

    user_profile.save()

    return response


@login_required
def ya_oauth_forbidden(request, type_of_oauth):
    oauth_error_text_header = ''
    oauth_error_text = (_(u'profil') + u' {0} ' + _(u'uzhe_privjazan')) \
        .format(request.session["ya_oauth_login"])
    if type_of_oauth == 'contest':
        oauth_error_text_header = _(u"privjazat_profil_kontesta")
    elif type_of_oauth == 'passport':
        oauth_error_text_header = _(u"privjazat_profil_ja")
    context = {
        'oauth_error_text_header': oauth_error_text_header,
        'oauth_error_text': oauth_error_text,
    }

    return render(request, 'oauth_error.html', context)


@login_required
def ya_oauth_changed(request):
    context = {
        'oauth_error_text_header': _(u"privjazat_profil_kontesta"),
        'oauth_error_text': _(u"pereprivjazat_tolko_svoj_profil"),
    }

    return render(request, 'oauth_error.html', context)


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
    issues = Issue.objects \
        .filter(student=user) \
        .exclude(task__type=Task.TYPE_MATERIAL) \
        .exclude(task__type=Task.TYPE_SEMINAR) \
        .order_by('-update_time')

    user_as_str = str(user.username) + '_tasks_filter'

    f = IssueFilterStudent(request.GET, issues)
    f.set_user(user)

    if f.form.data:
        request.session[user_as_str] = f.form.data
    elif user_as_str in request.session:
        f.form.data = request.session.get(user_as_str)

    f.form.helper = FormHelper(f.form)
    f.form.helper.form_method = 'get'
    f.form.helper.layout.append(
        HTML(u"""<div class="form-group row">
        <button id="button_filter" class="btn btn-secondary pull-xs-right" type="submit">{0}</button>
        </div>""".format(_(u'primenit')))
    )

    context = {
        'filter': f,
    }

    return render(request, 'my_tasks.html', context)


@login_required
def user_courses(request, username=None, year=None):
    user = request.user
    lang = user.profile.language

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

        tasks = Task.objects\
            .filter(course=course, groups__in=groups, is_hidden=False) \
            .exclude(type=Task.TYPE_MATERIAL)\
            .distinct()
        issues = Issue.objects.filter(student=user_to_show, task__in=tasks)

        if StudentCourseMark.objects.filter(student=user_to_show, course=course):
            mark = StudentCourseMark.objects.get(student=user_to_show, course=course).mark
        else:
            mark = None

        student_summ_score = issues \
            .filter(task__parent_task__isnull=True) \
            .filter(
                Q(task__type=Task.TYPE_SEMINAR)
                | Q(task__score_after_deadline=True)
                | ~Q(task__score_after_deadline=False, status_field__tag=IssueStatus.STATUS_ACCEPTED_AFTER_DEADLINE)
            ) \
            .distinct() \
            .aggregate(Sum('mark'))['mark__sum'] or 0

        new_course_statistics = dict()
        new_course_statistics['name'] = course.name
        new_course_statistics['url'] = course.get_absolute_url()

        new_course_statistics['issues_count'] = []
        for status in course.issue_status_system.statuses.all():
            new_course_statistics['issues_count'].append((status.color, status.get_name(lang),
                                                          issues.filter(status_field=status).count()))

        new_course_statistics['tasks'] = tasks.exclude(type=Task.TYPE_SEMINAR).count()
        new_course_statistics['mark'] = mark if mark else '--'
        new_course_statistics['summ_score'] = student_summ_score

        is_archive = int(not course.is_active)
        table_year = str(course.year)
        table_key = course.issue_status_system.id

        if table_year not in tables[is_archive]:
            tables[is_archive][table_year] = dict()

        if table_key in tables[is_archive][table_year]:
            tables[is_archive][table_year][table_key].append(new_course_statistics)
        else:
            tables[is_archive][table_year][table_key] = [new_course_statistics]

    context = {
        'tables': [sorted(x.items()) for x in tables],
        'current_year': str(current_year) if current_year is not None else '',
        'user_to_show': user_to_show,
        'user': user,
    }

    return render(request, 'user_courses.html', context)


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
                                                'invite': _(u'invajt_drugogo_kursa')}),
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
    user_profile = user.profile

    user_info = ''
    if 'user-info' in request.POST:
        user_info = request.POST['user-info'].strip()

    if user_info and not user_info.startswith(u'<div class="not-sanitize">'):
        user_info = u'<div class="not-sanitize">' + user_info + u'</div>'

    user_profile.info = user_info
    user_profile.save()

    return HttpResponse(json.dumps({'info': user_info}),
                        content_type="application/json")


def set_user_language(request):
    next = request.REQUEST.get('next')
    if not is_safe_url(url=next, host=request.get_host()):
        next = request.META.get('HTTP_REFERER')
        if not is_safe_url(url=next, host=request.get_host()):
            next = '/'
    response = HttpResponseRedirect(next)
    if request.method == 'POST':
        lang_code = request.POST.get('language', None)
        if 'ref' not in next:
            ref = urlparse(request.POST.get('referrer', next))
            response = HttpResponseRedirect('?ref='.join([next, ref.path]))
        if lang_code and check_for_language(lang_code):
            if hasattr(request, 'session'):
                request.session['django_language'] = lang_code
            else:
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)

        user = request.user
        if user.is_authenticated():
            user_profile = user.profile
            user_profile.language = lang_code
            user_profile.save()
    return response
