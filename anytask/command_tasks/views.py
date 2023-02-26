# -*- coding: utf-8 -*-

import json
import os.path

from reversion import revisions as reversion

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from django.views.decorators.http import require_http_methods

from common.timezone import get_datetime_with_tz, convert_datetime
from courses.models import Course
from groups.models import Group
from issues.model_issue_status import IssueStatus
from issues.models import Issue
from command_tasks.models import CommandTask


HEADERS = {'Authorization': 'OAuth ' + settings.CONTEST_OAUTH}
PROBLEMS_API = settings.CONTEST_API_URL + 'problems?locale={lang}&contestId={cont_id}'

templates_dir = os.path.join(os.path.dirname(__file__), 'templates/')


def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z


@login_required
def task_create_page(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if not course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        return task_create_or_edit(request, course)

    schools = course.school_set.all()
    seminar_tasks = CommandTask.objects.filter(type=CommandTask().TYPE_SEMINAR).filter(course=course)
    not_seminar_tasks = CommandTask.objects.filter(~Q(type=CommandTask().TYPE_SEMINAR)).filter(course=course)
    has_seminar = course.issue_status_system.statuses.filter(tag=IssueStatus.STATUS_SEMINAR).count()

    task_types = CommandTask.TASK_TYPE_CHOICES
    if not has_seminar:
        task_types = filter(lambda x: not x[0] == CommandTask.TYPE_SEMINAR, task_types)

    context = {
        'is_create': True,
        'course': course,
        'task_types': task_types,
        'seminar_tasks': seminar_tasks,
        'not_seminar_tasks': not_seminar_tasks,
        'contest_integrated': course.contest_integrated,
        'rb_integrated': course.rb_integrated,
        'hide_contest_settings': True if not course.contest_integrated else False,
        'school': schools[0] if schools else '',
        'user_location': request.user.profile.location,
        'geo_suggest_url': settings.GEO_SUGGEST_URL
    }

    print templates_dir
    return render(request, os.path.join(templates_dir, 'task_create.html'), context)


@login_required
def task_edit_page(request, task_id):
    task = get_object_or_404(CommandTask, id=task_id)

    if not task.course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        return task_create_or_edit(request, task.course, task_id)

    groups_required = []
    groups = task.groups.all()
    if task.type == task.TYPE_SEMINAR:
        children_groups = reduce(lambda x, y: x + y, [list(child.groups.all()) for child in task.children.all()], [])
        groups_required = set(children_groups).intersection(groups)
    else:
        for group in groups:
            if Issue.objects.filter(command_task=task, student__in=group.students.all()).count():
                groups_required.append(group)

    schools = task.course.school_set.all()

    seminar_tasks = CommandTask.objects.filter(type=CommandTask().TYPE_SEMINAR).filter(course=task.course)
    not_seminar_tasks = CommandTask.objects.filter(~Q(type=CommandTask().TYPE_SEMINAR)).filter(course=task.course)

    task_types = task.TASK_TYPE_CHOICES
    if task.type == task.TYPE_SEMINAR:
        task_types = filter(lambda x: not x[0] == task.TYPE_FULL, task_types)
    else:
        task_types = filter(lambda x: not x[0] == task.TYPE_SEMINAR, task_types)

    context = {
        'is_create': False,
        'course': task.course,
        'task': task,
        'task_types': task_types,
        'groups_required': groups_required,
        'show_help_msg_task_group': True if groups_required else False,
        'seminar_tasks': seminar_tasks,
        'not_seminar_tasks': not_seminar_tasks,
        'contest_integrated': task.contest_integrated,
        'rb_integrated': task.rb_integrated,
        'hide_contest_settings': True if not task.contest_integrated or task.type in [task.TYPE_SIMPLE,
                                                                                      task.TYPE_MATERIAL] else False,
        'school': schools[0] if schools else '',
        'user_location': request.user.profile.location,
        'geo_suggest_url': settings.GEO_SUGGEST_URL
    }

    return render(request, os.path.join(templates_dir, 'task_edit.html'), context)


def get_task_params(request, check_score_after_deadline=False):
    user = request.user
    task_title = request.POST.get('task_title', '').strip()
    task_short_title = request.POST.get('task_short_title', task_title).strip()
    max_score = int(request.POST.get('max_score') or 0)
    max_students = int(request.POST.get('max_students') or 0)
    max_commands = int(request.POST.get('max_commands') or 0)
    task_groups = Group.objects.filter(id__in=dict(request.POST)['task_group_id[]'])

    parent_id = request.POST.get('parent_id')
    parent = None
    if parent_id and parent_id != 'null':
        parent = get_object_or_404(CommandTask, id=int(parent_id))

    children = request.POST.getlist('children[]') or None
    if children == 'null':
        children = None

    task_deadline = request.POST.get('deadline') or None
    if task_deadline:
        task_deadline = get_datetime_with_tz(task_deadline, request.POST.get('geoid', None), user)

    score_after_deadline = True
    if check_score_after_deadline:
        score_after_deadline = 'score_after_deadline' in request.POST

    changed_task = 'changed_task' in request.POST
    task_type = request.POST.get('task_type', CommandTask().TYPE_FULL).strip()

    contest_integrated = False
    contest_id = 0
    problem_id = None
    simple_task_types = [CommandTask().TYPE_SIMPLE, CommandTask().TYPE_MATERIAL]
    if 'contest_integrated' in request.POST and task_type not in simple_task_types:
        contest_integrated = True
        contest_id = int(request.POST['contest_id'])
        problem_id = request.POST['problem_id'].strip()

    rb_integrated = 'rb_integrated' in request.POST and task_type not in simple_task_types
    one_file_upload = 'one_file_upload' in request.POST and rb_integrated
    accepted_after_contest_ok = 'accepted_after_contest_ok' in request.POST

    hidden_task = 'hidden_task' in request.POST
    task_text = request.POST.get('task_text', '').strip()

    nb_assignment_name = request.POST.get('nb_assignment_name')

    return {'attrs': {
        'updated_by': user,
        'title': task_title,
        'short_title': task_short_title,
        'score_max': max_score,
        'max_students': max_students,
        'max_commands': max_commands,
        'parent_task': parent,
        'deadline_time': task_deadline,
        'send_to_users': changed_task,
        'sended_notify': not changed_task,
        'type': task_type,
        'contest_integrated': contest_integrated,
        'contest_id': contest_id,
        'problem_id': problem_id,
        'rb_integrated': rb_integrated,
        'one_file_upload': one_file_upload,
        'accepted_after_contest_ok': accepted_after_contest_ok,
        'score_after_deadline': score_after_deadline,
        'is_hidden': hidden_task,
        'task_text': task_text,
        'nb_assignment_name': nb_assignment_name,
    },
        'children': children,
        'groups': task_groups
    }


def task_create_or_edit(request, course, task_id=None):
    params = get_task_params(request, course.issue_status_system.has_accepted_after_deadline())
    lang = request.user.profile.language

    changed_score_after_deadline = False
    if task_id:
        task = get_object_or_404(CommandTask, id=task_id)
        task_text = task.is_text_json()
        if task_text:
            task_title = json.loads(task.title, strict=False)
            task_title[lang] = params['attrs']['title']
            task_text[lang] = params['attrs']['task_text']
            params['attrs']['title'] = json.dumps(task_title, ensure_ascii=False)
            params['attrs']['task_text'] = json.dumps(task_text, ensure_ascii=False)
        changed_score_after_deadline = task.score_after_deadline != params['attrs']['score_after_deadline']
        params['attrs']['nb_assignment_name'] = task.nb_assignment_name
    else:
        task = CommandTask()
        task.course = course

    for attr_name, attr_value in params['attrs'].items():
        setattr(task, attr_name, attr_value)

    if task.parent_task:
        if task.parent_task.is_hidden:
            task.is_hidden = True
    task.save()

    for subtask in CommandTask.objects.filter(parent_task=task):
        subtask.is_hidden = task.is_hidden
        subtask.save()

    children = params['children']
    for course_task in CommandTask.objects.filter(course=course):
        if children and course_task.id in map(int, children):
            course_task.parent_task = task
            course_task.save()
        elif course_task.parent_task == task:
            course_task.parent_task = None
            course_task.save()

    task_groups = params['groups']
    task.groups = task_groups
    task.set_position_in_new_group(task_groups)

    if task_id and changed_score_after_deadline and task.parent_task:
        student_ids = User.objects.filter(group__in=task_groups).values_list('id', flat=True)
        for student_id in student_ids:
            parent_issue, created = Issue.objects.get_or_create(task_id=task.parent_task.id, student_id=student_id)
            total_mark = Issue.objects \
                .filter(task=task, student_id=student_id) \
                .exclude(task__is_hiddne=True) \
                .exclude(
                    task__score_after_deadline=False,
                    status_field__tag=IssueStatus.STATUS_ACCEPTED_AFTER_DEADLINE) \
                .aggregate(Sum('mark'))['mark__sum'] or 0
            if task.score_after_deadline:
                parent_issue.mark += total_mark
            else:
                parent_issue.mark -= total_mark
            parent_issue.set_status_seminar()

    if task.type == task.TYPE_SEMINAR:
        student_ids = User.objects.filter(group__in=task_groups).values_list('id', flat=True)
        for student_id in student_ids:
            issue, created = Issue.objects.get_or_create(task_id=task.id, student_id=student_id)
            issue.mark = Issue.objects \
                .filter(task__parent_task=task, student_id=student_id) \
                .exclude(task__is_hidden=True) \
                .exclude(
                    task__score_after_deadline=False,
                    status_field__tag=IssueStatus.STATUS_ACCEPTED_AFTER_DEADLINE) \
                .aggregate(Sum('mark'))['mark__sum'] or 0
            issue.set_status_seminar()

    task.save()
    reversion.set_user(request.user)
    if task_id:
        reversion.set_comment("Edit task")
    else:
        reversion.set_comment("Create task")

    return HttpResponse(json.dumps({'page_title': task.get_title(lang) + ' | ' + course.name + ' | ' + str(course.year),
                                    'redirect_page': '/task/edit/' + str(task.id) if not task_id else None}),
                        content_type="application/json")


def get_task_text_popup(request, task_id):
    task = get_object_or_404(CommandTask, id=task_id)

    context = {
        'task': task,
    }

    return render(request, os.path.join(templates_dir, 'task_text_popup.html'), context)


@login_required
@require_http_methods(['GET'])
def validate_nb_assignment_name(request):
    name = request.GET['nb_assignment_name']
    task_exists = CommandTask.objects.filter(nb_assignment_name=name).exists()
    if not task_exists:
        return HttpResponse(json.dumps(True))

    return HttpResponse(json.dumps(False))
