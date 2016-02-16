# encoding: utf-8

import logging

from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db import transaction

from tasks.models import Task, TaskTaken
from easy_ci.forms import RunForm, TaskTakenForm
from easy_ci.models import EasyCiTask, EasyCiCheck
from easy_ci.runner import CheckRunner

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

LOGGER = logging.getLogger('django.request')

@transaction.commit_on_success
def task_taken_submit(request, student_id, task_id):
    user = request.user
    student = get_object_or_404(User, id=student_id)
    task = get_object_or_404(Task, id=task_id)
    user_is_teacher = task.cource.user_is_teacher(user)
    if not (user_is_teacher or student == user):
        return HttpResponseForbidden()

    form = RunForm(request.POST)

    context = {
        'task' : task,
        'student' : student,
        'form' : form
    }

    if request.method != 'POST' or not form.is_valid():
        return render_to_response('run_submit.html', context, context_instance=RequestContext(request))

    if not form.cleaned_data['data']:
        return redirect(task_taken_view, student_id=student_id, task_id=task_id)

    easy_ci_task = form.instance
    easy_ci_task.student = student
    easy_ci_task.task = task
    form.save()
    easy_ci_task.save()

    runner = CheckRunner(easy_ci_task.data, easy_ci_task.task.title)
    try:
        exit_status, output = runner.run(EasyCiCheck.CHECK_ACTION_PEP8, easy_ci_task.student, task.group.name)
    except Exception as e:
        LOGGER.info("EasyCiQuickRunner=%s", e)
        return redirect(task_taken_view, student_id=student_id, task_id=task_id)

    easy_ci_check = EasyCiCheck()
    easy_ci_check.easy_ci_task = easy_ci_task
    easy_ci_check.type = EasyCiCheck.CHECK_ACTION_PEP8
    easy_ci_check.exit_status = exit_status
    easy_ci_check.output = output
    easy_ci_check.save()

    return redirect(task_taken_view, student_id=student_id, task_id=task_id)

def task_taken_view(request, student_id, task_id):
    if request.method == 'POST':
        return task_taken_submit(request, student_id, task_id)

    student = get_object_or_404(User, id=student_id)
    task = get_object_or_404(Task, id=task_id)
    user = request.user

    user_is_teacher = task.cource.user_is_teacher(user)
    if not (user_is_teacher or student == user):
        return HttpResponseForbidden()

    types_order = EasyCiCheck.TYPES_ORDER
    types_count = len(EasyCiCheck.TYPES)
    if not user_is_teacher:
        types_order = filter(lambda x : x not in EasyCiCheck.TYPES_HIDDEN, types_order)
        types_count -= len(EasyCiCheck.TYPES_HIDDEN)

    checks = {}

    runs = EasyCiTask.objects.filter(student=student).filter(task=task).order_by('added_time')
    for run in runs:
        _checks = run.easycicheck_set.all()
        if (not user_is_teacher):
            _checks = _checks.exclude(type__in=EasyCiCheck.TYPES_HIDDEN)
        _checks = sorted(_checks, key=lambda x: x.type)

        while (len(_checks) < types_count):
            _checks.append(EasyCiCheck())

        checks[run] = _checks

    context = {
        'runs' : runs,
        'task' : task,
        'hidden_types' : EasyCiCheck.TYPES_HIDDEN,
        'types_order' : types_order,
        'checks' : checks,
        'user_is_teacher' : user_is_teacher,
        'form' : RunForm(),
        'student' : student,
    }
    return render_to_response('task_taken_status.html', context, context_instance=RequestContext(request))


def check_task_view(request, easy_ci_task_id):
    easy_ci_task = get_object_or_404(EasyCiTask, id=easy_ci_task_id)
    student = easy_ci_task.student
    task = easy_ci_task.task
    user = request.user

    user_is_teacher = task.cource.user_is_teacher(user)
    if not (user_is_teacher or student == user):
        return HttpResponseForbidden()

    checks = EasyCiCheck.objects.filter(easy_ci_task=easy_ci_task).order_by('added_time')
    if not user_is_teacher:
        checks = checks.exclude(type__in=EasyCiCheck.TYPES_HIDDEN)

    is_last_task = True
    try:
        easy_ci_task.get_next_by_added_time()
        is_last_task = False
    except easy_ci_task.DoesNotExist:
        pass

    try:
        task_taken = TaskTaken.objects.get(task=task, user=student)
    except TaskTaken.DoesNotExist:
        task_taken = TaskTaken()

    task_taken.teacher_comments = easy_ci_task.teacher_comments

    if request.method == "POST":
        task_taken_form = TaskTakenForm(task.score_max, request.POST, instance=task_taken)
        if task_taken_form.is_valid():
            task_taken.task = task
            task_taken.user = student
            task_taken.scored_by = user
            task_taken.save()
            easy_ci_task.teacher_comments = task_taken.teacher_comments
            easy_ci_task.save()
            messages.add_message(request, messages.INFO,  message=u"Оценка сохранена")
            return redirect(check_task_view, easy_ci_task_id)
    else:
        task_taken_form = TaskTakenForm(task.score_max, instance=task_taken)

    context = {
        'easy_ci_task' : easy_ci_task,
        'is_last_task' : is_last_task,
        'code_html' : highlight(easy_ci_task.data, PythonLexer(), HtmlFormatter(linenos=True)),
        'styles' : HtmlFormatter().get_style_defs('.highlight'),
        'task' : task,
        'student' : student,
        'checks' : checks,
        'user_is_teacher' : user_is_teacher,
        'task_taken_form' : task_taken_form,
        'teachers_comments' : easy_ci_task.teacher_comments,
    }
    return render_to_response('output.html', context, context_instance=RequestContext(request))
