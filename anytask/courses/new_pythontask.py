# -*- coding: utf-8 -*-

from command_tasks.models import CommandTask, CommandTaskTaken
from issues.models import Issue
import os

from django.conf import settings
from django.db.models import Q
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponsePermanentRedirect

import datetime

from users.models import UserProfile

templates_dir = os.path.join(os.path.dirname(__file__), 'templates/')


class PythonTaskStat(object):
    def __init__(self, course_tasks):
        self.tasks = course_tasks
        self.group_stat = {}
        self.course_stat = {
            'total': 0.0,
            'active_students': 0,
            'avg_score': 0.0,
        }

    def update(self, group):
        self._group_update(group)
        self._course_update(group)

    def get_group_stat(self):
        return [(group, stat['student_stat']) for (group, stat) in self.group_stat.iteritems()]

    def get_course_stat(self):
        stat = [
            (group, stat['total'], stat['active_students'], stat['avg_score'])
            for (group, stat) in self.group_stat.iteritems()
        ]

        stat.append(
            (None, self.course_stat['total'], self.course_stat['active_students'], self.course_stat['avg_score'])
        )

        return stat

    def _student_stat(self, tasks, student):
        total = 0.0
        tasks_list = []

        for task in tasks:
            if student.id == task.first_user.id:
                score = task.first_user_score
            elif student.id == task.second_user.id:
                score = task.second_user_score
            elif student.id == task.third_user.id:
                score = task.third_user_score
            total += score
            tasks_list.append((task.task, task.score))

        return (total, tasks_list)

    def _group_update(self, group):
        stat = {
            'total': 0.0,
            'active_students': 0,
            'avg_score': 0.0,
            'student_stat': [],
        }

        group_students = []

        for student in group.students.filter(is_active=True).order_by('last_name', 'first_name'):
            tasks = CommandTaskTaken.objects.filter(
                Q(Q(first_user=student) | Q(second_user=student) | Q(third_user=student))
            ).filter(task__in=self.tasks)
            if tasks.count() > 0:
                stat['active_students'] += 1

            scores, student_tasks = self._student_stat(tasks, student)
            group_students.append((student, scores, student_tasks))
            stat['total'] += scores

        stat['student_stat'] = group_students

        if stat['active_students'] > 0:
            stat['avg_score'] = stat['total'] / stat['active_students']

        self.group_stat[group] = stat

    def _course_update(self, group):
        stat = self.group_stat[group]

        self.course_stat['total'] += stat['total']
        self.course_stat['active_students'] += stat['active_students']

        if self.course_stat['active_students'] > 0:
            self.course_stat['avg_score'] = self.course_stat['total'] / self.course_stat['active_students']
        else:
            self.course_stat['avg_score'] = 0.0


def tasks_list(request, course):
    user = request.user

    course.can_edit = course.user_can_edit_course(user)
    delta = datetime.timedelta(days=settings.PYTHONTASK_MAX_DAYS_WITHOUT_SCORES)
    task_and_task_taken = []
    for task in CommandTask.objects.filter(course=course).filter(parent_task=None).order_by('title'):
        task.add_user_properties(user)

        if task.task_text is None:
            task.task_text = ''

        task_taken_list = []
        for i, task_taken in enumerate(CommandTaskTaken.objects.filter(task=task).exclude(task__is_hidden=True).filter(
                Q(Q(status=CommandTaskTaken.STATUS_TAKEN) | Q(status=CommandTaskTaken.STATUS_SCORED)))):

            if settings.PYTHONTASK_MAX_DAYS_WITHOUT_SCORES and task_taken.status == CommandTaskTaken.STATUS_TAKEN:
                task_taken.cancel_date = task_taken.taken_time + delta

            task_taken.add_user_and_task_properties(user)
            task_taken_list.append((i + 1, task_taken))

        if task.has_subtasks():
            subtask_and_task_takens = []
            for subtask in CommandTask.objects.filter(parent_task=task).order_by('title'):
                subtask.add_user_properties(user)

                if subtask.task_text is None:
                    subtask.task_text = ''

                subtask_takens = list(CommandTaskTaken.objects.filter(task=subtask).exclude(task__is_hidden=True).exclude(
                    task__parent_task__is_hidden=True).filter(
                    Q(Q(status=CommandTaskTaken.STATUS_TAKEN) | Q(status=CommandTaskTaken.STATUS_SCORED))))
                for task_taken in subtask_takens:
                    task_taken.add_user_and_task_properties(user)
                if settings.PYTHONTASK_MAX_DAYS_WITHOUT_SCORES:
                    for subtask_taken in filter(lambda x: x.status == CommandTaskTaken.STATUS_TAKEN, subtask_takens):
                        subtask_taken.cancel_date = subtask_taken.taken_time + delta
                subtask_and_task_takens.append((subtask, subtask_takens))
            task_and_task_taken.append((task, subtask_and_task_takens))
        else:
            task_and_task_taken.append((task, task_taken_list))

    context = {
        'course': course,
        'user': user,
        'tasks_taken': task_and_task_taken,
        'user_is_teacher': course.user_is_teacher(user),
        'STATUS_TAKEN': CommandTaskTaken.STATUS_TAKEN,
        'STATUS_SCORED': CommandTaskTaken.STATUS_SCORED,
    }

    return render(request, os.path.join(templates_dir, 'course_tasks_potok_new.html'), context)


def python_stat(request, course):
    tasks = CommandTask.objects.filter(course=course)
    stat = PythonTaskStat(tasks)

    for group in course.groups.all().order_by('name'):
        stat.update(group)

    context = {
        'course': course,
        'group_stat': stat.get_group_stat(),
        'course_stat': stat.get_course_stat()
    }

    return render(request, 'statistics_new.html', context)


@login_required
@transaction.atomic
def get_task(request, course_id, task_id):
    user = request.user

    task = get_object_or_404(CommandTask, id=task_id)
    user_can_take_task, reason = task.user_can_take_task(user)
    if user_can_take_task:
        print task.max_students
        print task.max_students > 2
        third_user_enabled = (task.max_students > 2)
        task_taken, created = CommandTaskTaken.objects.get_or_create(first_user=user, task=task, third_user_enabled=third_user_enabled)
        task_taken.take()

        if not task_taken.issue:
            issue, created = Issue.objects.get_or_create(command_task=task, student=user)
            task_taken.issue = issue
            task_taken.save()

        task_taken.issue.add_comment(unicode(_(request.user.first_name + ' ' + request.user.last_name + ' ' + u"записался на задачу")))

    return redirect('courses.views.course_page', course_id=course_id)


@login_required
@transaction.atomic
def join_team(request, course_id, task_id, task_taken_id):
    user = request.user

    task = get_object_or_404(CommandTask, id=task_id)
    task_taken = get_object_or_404(CommandTaskTaken, id=task_taken_id)

    user_can_take_task, reason = task_taken.user_can_join_team(user)
    print reason

    if user_can_take_task:
        print 'lol'
        task_taken.join_team(user)

        if not task_taken.issue:
            issue, created = Issue.objects.get_or_create(task=task, student=user)
            task_taken.issue = issue
            task_taken.save()

        task_taken.issue.add_comment(unicode(_(request.user.first_name + ' ' + request.user.last_name + ' ' + u"записался на задачу")))

    return redirect('courses.views.course_page', course_id=course_id)


@login_required
@transaction.atomic
def score_task(request):
    course_id = request.GET.get('course_id', '')
    task_taken_id = request.GET.get('task_taken_id', '')
    student_id = request.GET.get('student_id', '')
    score = request.GET.get('score', '')

    task_taken = get_object_or_404(CommandTaskTaken, id=task_taken_id)
    student = get_object_or_404(UserProfile, id=student_id)

    task_taken.score_user(student, score)

    return redirect('courses.views.course_page', course_id=course_id)


@login_required
def cancel_task(request, course_id, task_id):
    user = request.user

    task = get_object_or_404(CommandTask, id=task_id)

    if task.user_can_cancel_task(user):
        task_taken = get_object_or_404(CommandTaskTaken, user=user, task=task)
        task_taken.cancel()

        if not task_taken.issue:
            issue, created = Issue.objects.get_or_create(task=task, student=user)
            task_taken.issue = issue
            task_taken.save()

        task_taken.issue.add_comment(u"{} {} {}".format(user.first_name, user.last_name, _(u"Отказался от задачи")))

    return redirect('courses.views.course_page', course_id=course_id)


@login_required
@transaction.atomic
def get_or_create_issue(request, task_id, task_taken_id):
    user = request.user

    task = get_object_or_404(CommandTask, id=task_id)
    task_taken = get_object_or_404(CommandTaskTaken, id=task_taken_id)

    return HttpResponsePermanentRedirect(
        "/issue/" + str(task_taken.issue.id))


