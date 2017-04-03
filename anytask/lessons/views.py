# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, get_object_or_404, redirect
from tasks.models import Task
from courses.models import Course
from groups.models import Group
from issues.model_issue_status import IssueStatus
from lessons.models import Lesson
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from tasks.models import TaskTaken, TaskGroupRelations
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from anycontest.common import get_contest_info, FakeResponse
from django.conf import settings
from django.utils.translation import ugettext as _

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
        return lesson_create_ot_edit(request, course)

    schools = course.school_set.all()

    context = {
        'is_create': True,
        'course': course,
        'school': schools[0] if schools else '',
    }

    return render_to_response('lesson_create.html', context, context_instance=RequestContext(request))


@login_required
def schedule_edit_page(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if not task.course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        return lesson_create_ot_edit(request, task.course, task_id)

    groups_required = []
    groups = task.groups.all()
    if task.type == task.TYPE_SEMINAR:
        children_groups = reduce(lambda x, y: x+y, [list(child.groups.all()) for child in task.children.all()], [])
        groups_required = set(children_groups).intersection(groups)
    else:
        for group in groups:
            if Issue.objects.filter(task=task, student__in=group.students.all()).count():
                groups_required.append(group)

    schools = task.course.school_set.all()

    seminar_tasks = Task.objects.filter(type=Task().TYPE_SEMINAR).filter(course=task.course)
    not_seminar_tasks = Task.objects.filter(~Q(type=Task().TYPE_SEMINAR)).filter(course=task.course)

    context = {
        'is_create': False,
        'course': task.course,
        'task': task,
        'task_types': task.TASK_TYPE_CHOICES[-1:] if task.type == task.TYPE_SEMINAR else task.TASK_TYPE_CHOICES[:-1],
        'groups_required': groups_required,
        'show_help_msg_task_group': True if groups_required else False,
        'seminar_tasks': seminar_tasks,
        'not_seminar_tasks': not_seminar_tasks,
        'contest_integrated': task.contest_integrated,
        'rb_integrated': task.rb_integrated,
        'hide_contest_settings': True if not task.contest_integrated
                                         or task.type in [task.TYPE_SIMPLE, task.TYPE_MATERIAL] else False,
        'school': schools[0] if schools else '',
    }

    return render_to_response('task_edit.html', context, context_instance=RequestContext(request))


def lesson_create_ot_edit(request, course, lesson_id=None):
    user = request.user
    lesson_title = request.POST['lesson_title'].strip()

    lesson_groups = Group.objects.filter(id__in=dict(request.POST)['lesson_group_id[]'])

    lesson_date = datetime.datetime.strptime(request.POST['date'], '%d-%m-%Y %H:%M')

    lesson_description = request.POST['lesson_text'].strip()

    if lesson_id:
        lssn = get_object_or_404(Lesson, id=lesson_id)
    else:
        lssn = Lesson()
        lssn.course = course

    lssn.title = lesson_title
    lssn.lesson_date = lesson_date
    lssn.description = lesson_description

    lssn.updated_by = user
    lssn.save()

    lssn.groups = lesson_groups
    lssn.set_position_in_new_group(lesson_groups)

    reversion.set_user(user)
    if lesson_id:
        reversion.set_comment("Edit task")
    else:
        reversion.set_comment("Create task")

    return HttpResponse(json.dumps({'page_title': lssn.title + ' | ' + course.name + ' | ' + str(course.year),
                                    'redirect_page': '/task/edit/' + str(lssn.id) if not lesson_id else None}),
                        content_type="application/json")