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