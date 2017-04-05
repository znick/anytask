
from tasks.models import Task, TaskTaken
from issues.models import Issue

from django.conf import settings
from django.db.models import Q
from django.db import transaction
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

import datetime



def tasks_list(request, course):
    user = request.user

    course.can_edit = course.user_can_edit_course(user)
    delta = datetime.timedelta(days=settings.PYTHONTASK_MAX_DAYS_WITHOUT_SCORES)
    task_and_task_taken = []
    for task in Task.objects.filter(course=course).filter(parent_task=None).order_by('weight'):
        task.add_user_properties(user)

        if task.task_text is None:
            task.task_text = ''

        task_taken_list = []
        for task_taken in TaskTaken.objects.filter(task=task).exclude(task__is_hidden=True).filter(Q( Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED))):
            if settings.PYTHONTASK_MAX_DAYS_WITHOUT_SCORES and task_taken.status == TaskTaken.STATUS_TAKEN:
                task_taken.cancel_date = task_taken.added_time + delta
            task_taken_list.append(task_taken)

        if task.has_subtasks():
            subtask_and_task_takens = []
            for subtask in Task.objects.filter(parent_task=task).order_by('weight'):
                subtask.add_user_properties(user)

                if subtask.task_text is None:
                    subtask.task_text = ''

                subtask_takens = list(TaskTaken.objects.filter(task=subtask).exclude(task__is_hidden=True).exclude(task__parent_task__is_hidden=True).filter(Q( Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED))))
                if settings.PYTHONTASK_MAX_DAYS_WITHOUT_SCORES:
                    for subtask_taken in filter(lambda x: x.status == TaskTaken.STATUS_TAKEN, subtask_takens):
                        subtask_taken.cancel_date = subtask_taken.added_time + delta
                subtask_and_task_takens.append((subtask, subtask_takens))
            task_and_task_taken.append((task, subtask_and_task_takens))
        else:
            task_and_task_taken.append((task, task_taken_list))

    context = {
        'course'        : course,
        'tasks_taken'   : task_and_task_taken,
        'STATUS_TAKEN'  : TaskTaken.STATUS_TAKEN,
        'STATUS_SCORED' : TaskTaken.STATUS_SCORED,
    }

    return render_to_response('course_tasks_potok.html', context, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def get_task(request, course_id, task_id):
    user = request.user

    task = get_object_or_404(Task, id=task_id)
    user_can_take_task, reason = task.user_can_take_task(user)
    if user_can_take_task:
        task_taken, _ = TaskTaken.objects.get_or_create(user=user, task=task)
        task_taken.status = TaskTaken.STATUS_TAKEN

        if not task_taken.issue:
            issue, created = Issue.objects.get_or_create(task=task, student=user)
            task_taken.issue = issue

        task_taken.save()

    return redirect('courses.views.course_page', course_id=course_id)

@login_required
def cancel_task(request, course_id, task_id):
    user = request.user

    task = get_object_or_404(Task, id=task_id)

    if task.user_can_cancel_task(user):
        task_taken = get_object_or_404(TaskTaken, user=user, task=task)
        task_taken.status = TaskTaken.STATUS_CANCELLED
        task_taken.save()

        return redirect('courses.views.course_page', course_id=course_id)
