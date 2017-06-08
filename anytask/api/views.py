import base64
import json

from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login

from courses.models import Course, DefaultTeacher, StudentCourseMark, MarkField, FilenameExtension
from tasks.models import Task


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

        username, password = base64.b64decode(auth_str_parts[1]).split(":", 1)
        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return get_401_response()

        login(request, user)
        request.user = user
        return view(request, *args, **kwargs)
    return check_auth

def unpack_issue(issue):
    return {
        "mark": issue.mark,
        "create_time": issue.create_time,
        "update_time": issue.update_time,
        "responsible": issue.responsible.username,
        "followers": map(issue.followers, lambda x: x.username),
        "status": issue.get_status(),
    }


@login_required_basic_auth
def get_issues(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user = request.user

    issues = []
    if not course.user_is_teacher(user):
        return HttpResponseForbidden

    for task in Course.task_set():
        for issue in task.issue_set():
            issues.append(unpack_issue(issue))

    return HttpResponse(json.dumps(issues),
                        content_type="application/json")
