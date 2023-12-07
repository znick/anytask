# -*- coding: utf-8 -*-

import datetime
import json
import uuid

from reversion import revisions as reversion
from courses.models import Course
from common.timezone import get_datetime_with_tz
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from groups.models import Group
from lessons.models import Lesson


@login_required
def schedule_create_page(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if not course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        return lesson_create(request, course)

    schools = course.school_set.all()

    context = {
        'is_create': True,
        'course': course,
        'period_types': Lesson().PERIOD_CHOICES,
        'school': schools[0] if schools else '',
        'user_location': request.user.profile.location,
        'geo_suggest_url': settings.GEO_SUGGEST_URL
    }

    return render(request, 'lesson_create.html', context)


@login_required
def schedule_edit_page(request, lesson_id):
    lssn = get_object_or_404(Lesson, id=lesson_id)

    if not lssn.course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        return lesson_edit(request, lssn.course, lesson_id)

    schools = lssn.course.school_set.all()

    context = {
        'is_create': False,
        'course': lssn.course,
        'lesson': lssn,
        'period_types': lssn.PERIOD_CHOICES,
        'school': schools[0] if schools else '',
        'user_location': request.user.profile.location,
        'geo_suggest_url': settings.GEO_SUGGEST_URL
    }

    return render(request, 'lesson_edit.html', context)


def get_lesson_dates(date_startime, date_endtime, date_end, week_days):
    lesson_dates = []
    delta_days = (date_end - date_startime).days
    for i in range(delta_days + 1):
        curr_date_start = date_startime + datetime.timedelta(days=i)
        curr_date_end = date_endtime + datetime.timedelta(days=i)
        if curr_date_start.weekday() in week_days:
            lesson_dates.append((curr_date_start, curr_date_end))
    return lesson_dates


def get_params(request_dict, user):
    params = dict()
    params['lesson_title'] = request_dict['lesson_title'].strip()
    if 'lesson_group_id[]' in request_dict:
        params['lesson_groups'] = Group.objects.filter(id__in=dict(request_dict)['lesson_group_id[]'])
    params['period'] = request_dict['period_type'].strip()
    geoid = request_dict['geoid']
    params['date_starttime'] = get_datetime_with_tz(request_dict['lesson_date_start'], geoid, user)
    params['date_endtime'] = get_datetime_with_tz(request_dict['lesson_date_finish'], geoid, user)
    if params['period'] != 'Once':
        params['date_end'] = get_datetime_with_tz(request_dict['date_end'], geoid, user)
        week_days = list(map(int, (dict(request_dict)['days[]'])))
        params['lesson_dates'] = \
            get_lesson_dates(params['date_starttime'], params['date_endtime'], params['date_end'], week_days)
        params['lesson_days'] = ','.join(dict(request_dict)['days[]'])
    else:
        params['date_end'] = params['date_endtime']
        params['lesson_dates'] = [(params['date_starttime'], params['date_endtime'])]
        params['lesson_days'] = ''

    params['lesson_description'] = request_dict['lesson_text'].strip()
    return params


def set_params(params, course, group, user, schedule_id, lssn_date, lesson=None):
    lssn = Lesson() if not lesson else lesson
    lssn.title = params['lesson_title']
    lssn.course = course
    lssn.schedule_id = schedule_id
    lssn.date_starttime = lssn_date[0]
    lssn.date_endtime = lssn_date[1]
    lssn.period = params['period']
    lssn.date_end = params['date_end']
    lssn.days = params['lesson_days']
    lssn.description = params['lesson_description']
    lssn.updated_by = user
    lssn.group = group
    lssn.save()
    lssn.set_position()
    return lssn.id


def lesson_create(request, course):
    user = request.user
    params = get_params(request.POST, user)
    for group in params['lesson_groups']:
        schedule_id = uuid.uuid1().hex
        for lssn_date in params['lesson_dates']:
            lssn_id = set_params(params, course, group, user, schedule_id, lssn_date)

    reversion.set_user(user)
    reversion.set_comment("Create lesson")

    return HttpResponse(json.dumps({'page_title': ' | '.join([params['lesson_title'], course.name, str(course.year)]),
                                    'redirect_page': '/lesson/edit/' + str(lssn_id)}),
                        content_type="application/json")


def need_delete(lesson, new_params):
    if lesson.date_starttime.date() != new_params['date_starttime'].date() \
            or lesson.date_end.date() != new_params['date_end'].date() \
            or lesson.days != new_params['lesson_days']:
        return True
    return False


def lesson_edit(request, course, lesson_id):
    user = request.user
    lesson = get_object_or_404(Lesson, id=lesson_id)
    schedule_id = lesson.schedule_id
    group = lesson.group
    params = get_params(request.POST, request.user)

    if 'change_all' not in request.POST:
        set_params(params, course, group, user, schedule_id, params['lesson_dates'][0], lesson)
    else:
        if need_delete(lesson, params):
            Lesson.objects.filter(
                schedule_id=schedule_id,
                date_starttime__gte=lesson.date_starttime
            ).delete()
            for i, lssn_date in enumerate(params['lesson_dates']):
                set_params(params, course, group, user, schedule_id, lssn_date, None)

        else:
            lesson_changed = Lesson.objects.filter(
                schedule_id=schedule_id,
                date_starttime__gte=lesson.date_starttime
            )
            i = j = 0
            while i < len(lesson_changed):
                if lesson_changed[i].date_starttime.date() != params['lesson_dates'][j][0].date():
                    j += 1
                else:
                    set_params(params, course, group, user, schedule_id, params['lesson_dates'][j], lesson_changed[i])
                    i += 1

    reversion.set_user(user)
    reversion.set_comment("Edit lesson")

    return HttpResponse(json.dumps({'page_title': ' | '.join([lesson.title, course.name, str(course.year)]),
                                    'redirect_page': None}),
                        content_type="application/json")
