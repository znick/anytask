# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from django.core.exceptions import PermissionDenied

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML

from courses.models import StudentCourseMark
from courses.models import Course
from users.models import UserProfile, IssueFilterStudent, UserProfileFilter, UserStatus


@require_http_methods(['GET'])
@login_required
def staff_page(request):
    user = request.user

    if not user.is_staff:
        raise PermissionDenied

    user_profiles = UserProfile.objects.all()

    user_as_str = str(user.username) + '_userprofiles_filter'

    f = UserProfileFilter(request.GET, user_profiles)
    f.set()

    if f.form.data:
        request.session[user_as_str] = f.form.data
    elif user_as_str in request.session:
        f.form.data = request.session.get(user_as_str)

    f.form.helper = FormHelper(f.form)
    f.form.helper.form_method = 'get'
    f.form.helper.layout.append(HTML(u"""<div class="form-group row">
        <button id="button_filter" class="btn btn-secondary pull-xs-right" type="submit">Применить</button>
</div>"""))

    context = {
        'filter': f,
    }

    return render_to_response('staff.html', context, context_instance=RequestContext(request))


@require_http_methods(['GET'])
@login_required
def get_gradebook(request):
    user = request.user

    if not user.is_staff:
        raise PermissionDenied

    statuses = UserStatus.objects.filter(type='activity')

    context = {
        'statuses': statuses,
    }

    return render_to_response('get_gradebook.html', context, context_instance=RequestContext(request))


@require_http_methods(['GET'])
@login_required
def gradebook_page(request, statuses=None):
    user = request.user

    if not user.is_staff:
        raise PermissionDenied

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
                mark = '--'
            marks_for_student.append(mark if mark else '')
        entry['marks'] = marks_for_student
        students_with_marks.append(entry)

    context = {
        'students': students_with_marks,
        'courses': courses,
    }

    return render_to_response('gradebook.html', context, context_instance=RequestContext(request))
