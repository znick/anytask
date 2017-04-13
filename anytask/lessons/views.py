# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, get_object_or_404, redirect
from tasks.models import Task
from courses.models import Course
from groups.models import Group
from issues.model_issue_status import IssueStatus
from lessons.models import Lesson, Schedule
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.conf import settings

import datetime
import reversion
import requests
import json


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
    }

    return render_to_response('lesson_create.html', context, context_instance=RequestContext(request))


@login_required
def schedule_edit_page(request, lesson_id):
    lssn = get_object_or_404(Lesson, id=lesson_id)
    schedule_id = lssn.schedule_id

    if not lssn.course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        return lesson_edit(request, lssn.course, lesson_id, schedule_id)
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
        'groups_required': groups_required,
        'school': schools[0] if schools else '',
    }

    return render_to_response('lesson_edit.html', context, context_instance=RequestContext(request))


def get_lesson_dates(date_start, date_end, week_days):
    lesson_dates = []
    delta_days = (date_end - date_start).days
    for i in xrange(delta_days + 1):
        curr_date = date_start + datetime.timedelta(days=i)
        if curr_date.weekday() in week_days:
            lesson_dates.append(curr_date)
    return lesson_dates


def lesson_create(request, course):
    user = request.user
    lesson_groups = Group.objects.filter(id__in=dict(request.POST)['lesson_group_id[]'])

    period = request.POST['period_type'].strip()
    date_start = datetime.datetime.strptime(request.POST['date_start'], '%d-%m-%Y %H:%M')
    if period != 'Once':
        date_end = datetime.datetime.strptime(request.POST['date_end'], '%d-%m-%Y %H:%M')
        week_days = list(map(int, (dict(request.POST)['days[]'])))
        lesson_dates = get_lesson_dates(date_start, date_end, week_days)
        lesson_days = ','.join(dict(request.POST)['days[]'])
    else:
        date_end = date_start
        lesson_dates = [date_start]
        lesson_days = ''

    lesson_description = request.POST['lesson_text'].strip()

    schedule_id = int(datetime.datetime.now().strftime('%d%m%Y%H%M'))

    for lssn_date in lesson_dates:
        lssn = Lesson()
        lssn.course = course
        lssn.schedule_id = schedule_id
        lssn.lesson_date = lssn_date
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


def schedule_create_ot_edit(request, course, subject_id=None):
    user = request.user
    subject_groups = Group.objects.filter(id__in=dict(request.POST)['lesson_group_id[]'])
    subject_period = request.POST['period_type'].strip()
    subject_date_start = datetime.datetime.strptime(request.POST['date_start'], '%d-%m-%Y %H:%M')
    if subject_period != 'Once':
        subject_date_end = datetime.datetime.strptime(request.POST['date_end'], '%d-%m-%Y %H:%M')
        subject_days = ','.join(dict(request.POST)['days[]'])
    else:
        subject_date_end = subject_date_start
        subject_days = ''
    subject_description = request.POST['subject_text'].strip()

    for group in subject_groups:
        if subject_id:
            subject = get_object_or_404(Schedule, id=subject_id)
        else:
            subject = Schedule()
            subject.course = course

        subject.date_start = subject_date_start
        subject.date_end = subject_date_end
        subject.days = subject_days
        subject.description = subject_description
        subject.group = group
        subject.updated_by = user

        if subject_period in dict(subject.PERIOD_CHOICES):
            subject.period = subject_period
        else:
            subject.period = subject.PERIOD_SIMPLE

        subject.save()

    reversion.set_user(user)
    if subject_id:
        reversion.set_comment("Edit schedule")
    else:
        reversion.set_comment("Create schedule")

    return HttpResponse(json.dumps({'page_title': subject.subject + ' | ' + course.name + ' | ' + str(course.year),
                                    'redirect_page': '/lesson/edit/' + str(subject.id) if not subject_id else None}),
                        content_type="application/json")