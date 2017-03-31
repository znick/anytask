# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML

from courses.models import StudentCourseMark
from users.models import UserProfile
from users.model_user_profile_filter import UserProfileFilter
from users.model_user_status import UserStatus, get_statuses


import csv
import logging
import json

logger = logging.getLogger('django.request')

MAX_FILE_SIZE = settings.FILE_UPLOAD_MAX_MEMORY_SIZE
SEARCH_FIELDS = {
    'login': 'user__username',
    'email': 'user__email',
}


@login_required
def staff_page(request):
    user = request.user

    if not user.is_staff:
        raise PermissionDenied

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

    return render_to_response('staff.html', context, context_instance=RequestContext(request))


@require_http_methods(['POST'])
@login_required
def ajax_change_status(request):
    if not request.is_ajax():
        return HttpResponseForbidden()

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
        return HttpResponseForbidden()

    post_dict = dict(request.POST)
    if 'user_ids[]' in post_dict:
        index = save_to_session(request, post_dict['user_ids[]'])
    else:
        return HttpResponseForbidden()

    return HttpResponse(json.dumps({'index': index}), content_type="application/json")


def save_to_session(request, user_ids):
    index = request.session.get('user_ids_send_mail_counter', -1) + 1
    request.session['user_ids_send_mail_counter'] = index
    request.session['user_ids_send_mail_' + str(index)] = user_ids

    return index


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
                mark = None
            marks_for_student.append(mark if mark else '--')
        entry['marks'] = marks_for_student
        students_with_marks.append(entry)

    context = {
        'students': students_with_marks,
        'courses': courses,
    }

    return render_to_response('gradebook.html', context, context_instance=RequestContext(request))
