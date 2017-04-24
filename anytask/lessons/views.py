# -*- coding: utf-8 -*-

import datetime
import json

import reversion
from courses.models import Course
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from groups.models import Group
from lessons.models import Lesson


@login_required
def schedule_create_page(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if not course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        return lesson_create_or_edit(request, course)

    schools = course.school_set.all()

    context = {
        'is_create': True,
        'course': course,
        'period_types': Lesson().PERIOD_CHOICES,
        'school': schools[0] if schools else '',
    }

    return render_to_response('lesson_create.html', context, context_instance=RequestContext(request))


@login_required
def schedule_edit_page(request, lesson_id):
    lssn = get_object_or_404(Lesson, id=lesson_id)

    if not lssn.course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        return lesson_create_or_edit(request, lssn.course, lesson_id)
    students = set(lssn.visited_students.all())
    groups_required = []
    groups = lssn.groups.all()
    for group in groups:
        if students.intersection(set(group.students.all())):
            groups_required.append(group)

    schools = lssn.course.school_set.all()

    context = {
        'is_create': False,
        'course': lssn.course,
        'lesson': lssn,
        'period_types': lssn.PERIOD_CHOICES,
        'groups_required': groups_required,
        'school': schools[0] if schools else '',
        'show_help_msg_lssn_group': True if groups_required else False
    }

    return render_to_response('lesson_edit.html', context, context_instance=RequestContext(request))


def get_lesson_dates(date_startime, date_endtime, date_end, week_days):
    lesson_dates = []
    delta_days = (date_end - date_startime).days
    for i in xrange(delta_days + 1):
        curr_date_start = date_startime + datetime.timedelta(days=i)
        curr_date_end = date_endtime + datetime.timedelta(days=i)
        if curr_date_start.weekday() in week_days:
            lesson_dates.append((curr_date_start, curr_date_end))
    return lesson_dates


def lesson_create_or_edit(request, course, lesson_id=None):
    user = request.user
    lesson_title = request.POST['lesson_title'].strip()
    lesson_groups = Group.objects.filter(id__in=dict(request.POST)['lesson_group_id[]'])
    period = request.POST['period_type'].strip()
    date_starttime = datetime.datetime.strptime(request.POST['lesson_date_start'], '%d-%m-%Y %H:%M')
    date_endtime = datetime.datetime.strptime(request.POST['lesson_date_finish'], '%d-%m-%Y %H:%M')
    if period != 'Once':
        date_end = datetime.datetime.strptime(request.POST['date_end'], '%d-%m-%Y %H:%M')
        week_days = list(map(int, (dict(request.POST)['days[]'])))
        lesson_dates = get_lesson_dates(date_starttime, date_endtime, date_end, week_days)
        lesson_days = ','.join(dict(request.POST)['days[]'])
    else:
        date_end = date_endtime
        lesson_dates = [(date_starttime, date_endtime)]
        lesson_days = ''

    lesson_description = request.POST['lesson_text'].strip()

    create_new = True
    if lesson_id:
        lssn = get_object_or_404(Lesson, id=lesson_id)
        schedule_id = lssn.schedule_id
        if 'change_all' not in request.POST:
            lesson_dates = [(date_starttime, date_endtime)]
            create_new = False
        else:
            Lesson.objects.filter(schedule_id=schedule_id, date_starttime__gte=date_starttime.date()).delete()
    else:
        schedule_id = int(datetime.datetime.now().strftime('%d%m%Y%H%M%S'))

    for lssn_date in lesson_dates:
        lssn = Lesson() if create_new else lssn
        lssn.title = lesson_title
        lssn.course = course
        lssn.schedule_id = schedule_id
        lssn.date_starttime = lssn_date[0]
        lssn.date_endtime = lssn_date[1]
        lssn.period = period
        lssn.date_end = date_end
        lssn.days = lesson_days
        lssn.description = lesson_description
        lssn.updated_by = user
        lssn.save()

        lssn.groups = lesson_groups
        lssn.set_position_in_new_group(lesson_groups)

    reversion.set_user(user)
    reversion.set_comment("Create lesson")

    return HttpResponse(json.dumps({'page_title': str(schedule_id) + ' | ' + course.name + ' | ' + str(course.year),
                                    'redirect_page': '/lesson/edit/' + str(schedule_id)}),
                        content_type="application/json")
