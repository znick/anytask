from __future__ import unicode_literals

import base64
import json

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from courses.models import Course
from issues.models import Issue
from users.models import UserProfile

ISSUE_FILTER = {
    'student': 'student__username',
    'responsible': 'responsible__username'
}


def login_required_basic_auth(view):
    def get_401_response():
        response = HttpResponse()
        response.status_code = 401
        response['WWW-Authenticate'] = 'Basic realm="AnyTask API"'
        return response

    def check_auth(request, *args, **kwargs):
        if 'HTTP_AUTHORIZATION' not in request.META:
            return get_401_response()

        auth_str = request.META['HTTP_AUTHORIZATION']
        auth_str_parts = auth_str.split()

        if auth_str_parts[0].lower() != "basic":
            return get_401_response()

        username, password = base64.b64decode(auth_str_parts[1].encode('utf8')).decode('utf8').split(":", 1)
        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return get_401_response()

        login(request, user)
        request.user = user
        return view(request, *args, **kwargs)

    return check_auth


def unpack_user(user):
    profile = user.profile
    return {
        "id": user.id,
        "name": user.get_full_name(),
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "middle_name": profile.middle_name,
    }


def unpack_task(task, lang=settings.API_LANGUAGE_CODE):
    return {
        "id": task.id,
        "title": task.get_title(lang),
    }


def unpack_issue(issue, add_events=False, request=None, lang=settings.API_LANGUAGE_CODE):
    task = issue.task
    ret = {
        "id": issue.id,
        "mark": issue.mark,
        "create_time": issue.create_time.isoformat() + "Z",
        "update_time": issue.update_time.isoformat() + "Z",
        "responsible": None,
        "followers": list(map(lambda x: unpack_user(x), issue.followers.all())),
        "status": unpack_status(issue.status_field, lang),
        "student": unpack_user(issue.student),
        "task": unpack_task(task)
    }

    if issue.responsible:
        ret["responsible"] = unpack_user(issue.responsible)

    if add_events and request:
        ret["events"] = list(map(lambda x: unpack_event(request, x), issue.get_history()))

    return ret


def unpack_file(request, f):
    return {
        "id": f.id,
        "filename": f.filename(),
        "path": f.file.url,
        "url": request.build_absolute_uri(f.file.url),
    }


def has_access(user, issue):
    if user in (issue.student,
                issue.responsible):
        return True

    if issue.followers.filter(id=user.id).exists():
        return True

    course = issue.task.course
    if course.user_is_teacher(user):
        return True

    return False


def unpack_event(request, event):
    ret = {
        "id": event.id,
        "timestamp": event.timestamp.isoformat() + "Z",
        "author": unpack_user(event.author),
        "message": event.get_message(),
        # "files": list(event.file_set.all())
        "files": list(map(lambda x: unpack_file(request, x), event.file_set.filter(deleted=False))),
    }

    return ret


def unpack_status(status, lang=settings.API_LANGUAGE_CODE):
    return {
        "id": status.id,
        "name": status.get_name(lang),
        "tag": status.tag,
        "color": status.color,
    }


def unpack_statuses(course, lang=settings.API_LANGUAGE_CODE):
    ret = []

    for status in course.issue_status_system.statuses.all():
        ret.append(unpack_status(status, lang))

    ret = sorted(ret, key=lambda x: x[u'id'])
    return ret


def get_issue_filter(data):
    filter_args = {}
    if 'status' in data:
        status_arg = data['status']
        filter_args['status_field__id' if status_arg.isdigit() else 'status_field__tag'] = status_arg

    for arg, qs_arg in ISSUE_FILTER.items():
        if arg in data:
            filter_args[qs_arg] = data[arg]

    return filter_args


@login_required_basic_auth
@require_http_methods(['GET'])
def get_issues(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user = request.user
    if not course.user_is_teacher(user):
        return HttpResponseForbidden()

    add_events = bool(request.GET.get("add_events", False))
    filter_args = get_issue_filter(request.GET)

    ret = []
    issues = Issue.objects \
        .filter(task__course=course, **filter_args) \
        .select_related("task") \
        .prefetch_related("followers")
    lang = request.GET.get('lang', settings.API_LANGUAGE_CODE)
    for issue in issues:
        ret.append(unpack_issue(issue, add_events=add_events, request=request, lang=lang))

    return HttpResponse(json.dumps(ret),
                        content_type="application/json")


def get_issue(request, issue):
    lang = request.GET.get('lang', settings.API_LANGUAGE_CODE)
    ret = unpack_issue(issue, add_events=True, request=request, lang=lang)

    return HttpResponse(json.dumps(ret),
                        content_type="application/json")


def post_issue(request, issue):
    user = request.user

    if issue.task.course.user_is_teacher(user):
        status = request.POST.get('status')
        if status:
            if status.isdigit():
                issue.set_status_by_id(status, user)
            else:
                issue.set_status_by_tag(status, user)

        mark = request.POST.get('mark')
        if mark:
            try:
                issue.set_byname('mark', float(mark))
            except ValueError:
                return HttpResponseBadRequest()

    comment = request.POST.get('comment')
    if comment:
        issue.add_comment(comment, author=user)

    lang = request.POST.get('lang', settings.API_LANGUAGE_CODE)
    ret = unpack_issue(get_object_or_404(Issue, id=issue.id), add_events=True, request=request, lang=lang)

    return HttpResponse(json.dumps(ret),
                        content_type="application/json")


@csrf_exempt
@login_required_basic_auth
@require_http_methods(['GET', 'POST'])
def get_or_post_issue(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)

    if not has_access(request.user, issue):
        return HttpResponseForbidden()

    if request.method == 'POST':
        return post_issue(request, issue)
    return get_issue(request, issue)


@csrf_exempt
@login_required_basic_auth
@require_http_methods(['POST'])
def add_comment(request, issue_id):
    comment = request.POST.get('comment')
    if not comment:
        return HttpResponseBadRequest()

    user = request.user
    issue = get_object_or_404(Issue, id=issue_id)

    if not has_access(user, issue):
        return HttpResponseForbidden()

    issue.add_comment(comment, author=user)

    return HttpResponse(status=201)


@login_required_basic_auth
@require_http_methods(['GET'])
def get_issue_statuses(request, course_id):
    user = request.user
    course = get_object_or_404(Course, id=course_id)

    if not course.user_is_teacher(user):
        return HttpResponseForbidden()

    ret = unpack_statuses(course)

    return HttpResponse(json.dumps(ret),
                        content_type="application/json")


@require_http_methods(['GET'])
def check_user(request):
    ya_login = request.GET.get('ya_login')
    if not ya_login:
        return HttpResponseBadRequest()

    try:
        profile = UserProfile.objects.select_related('user').get(ya_passport_login=ya_login)
    except UserProfile.DoesNotExist:
        return HttpResponseNotFound('No profile found')

    user = profile.user

    return HttpResponse(json.dumps({
        'id': user.id,
        'ya_passport_login': ya_login,
        'active': user.is_active,
        'is_staff': user.is_staff or user.is_superuser,
        'is_teacher': user.course_teachers_set.exists(),
    }), content_type="application/json")
