# -*- coding: utf-8 -*-

import datetime
import json

import requests
import reversion

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from anycontest.common import get_contest_info, FakeResponse
from courses.models import Course
from groups.models import Group
from issues.model_issue_status import IssueStatus
from issues.models import Issue
from tasks.models import Task


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
    seminar_tasks = Task.objects.filter(type=Task().TYPE_SEMINAR).filter(course=course)
    not_seminar_tasks = Task.objects.filter(~Q(type=Task().TYPE_SEMINAR)).filter(course=course)
    has_seminar = course.issue_status_system.statuses.filter(tag=IssueStatus.STATUS_SEMINAR).count()

    context = {
        'is_create': True,
        'course': course,
        'task_types':  Task().TASK_TYPE_CHOICES if has_seminar else Task().TASK_TYPE_CHOICES[:-1],
        'seminar_tasks': seminar_tasks,
        'not_seminar_tasks': not_seminar_tasks,
        'contest_integrated': course.contest_integrated,
        'rb_integrated': course.rb_integrated,
        'hide_contest_settings': True if not course.contest_integrated else False,
        'school': schools[0] if schools else '',
    }

    return render_to_response('task_create.html', context, context_instance=RequestContext(request))


@login_required
def task_import_page(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if not course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    schools = course.school_set.all()

    seminar_tasks = Task.objects.filter(type=Task().TYPE_SEMINAR).filter(course=course)

    context = {
        'is_create': True,
        'course': course,
        'rb_integrated': course.rb_integrated,
        'school': schools[0] if schools else '',
        'seminar_tasks': seminar_tasks,
    }

    return render_to_response('task_import.html', context, context_instance=RequestContext(request))


@login_required
def contest_import_page(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if not course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    schools = course.school_set.all()

    seminar_tasks = Task.objects.filter(type=Task().TYPE_SEMINAR).filter(course=course)

    context = {
        'is_create': True,
        'course': course,
        'rb_integrated': course.rb_integrated,
        'seminar_tasks': seminar_tasks,
        'school': schools[0] if schools else '',
        'contest_import': True,
    }

    return render_to_response('contest_import.html', context, context_instance=RequestContext(request))


@login_required
def task_edit_page(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if not task.course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        return task_create_or_edit(request, task.course, task_id)

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


def get_task_params(request, check_score_after_deadline=False):
    user = request.user
    task_title = request.POST.get('task_title', '').strip()
    task_short_title = request.POST.get('task_short_title', task_title).strip()
    max_score = int(request.POST.get('max_score') or 0)
    task_groups = Group.objects.filter(id__in=dict(request.POST)['task_group_id[]'])

    parent_id = request.POST.get('parent_id')
    parent = None
    if parent_id and parent_id != 'null':
        parent = get_object_or_404(Task, id=int(parent_id))

    children = request.POST.getlist('children[]') or None
    if children == 'null':
        children = None

    task_deadline = request.POST.get('deadline') or None
    if task_deadline:
        task_deadline = datetime.datetime.strptime(task_deadline, '%d-%m-%Y %H:%M')

    score_after_deadline = True
    if check_score_after_deadline:
        score_after_deadline = 'score_after_deadline' in request.POST

    changed_task = 'changed_task' in request.POST
    task_type = request.POST.get('task_type', Task().TYPE_FULL).strip()

    contest_integrated = False
    contest_id = 0
    problem_id = None
    simple_task_types = [Task().TYPE_SIMPLE, Task().TYPE_MATERIAL]
    if 'contest_integrated' in request.POST and task_type not in simple_task_types:
        contest_integrated = True
        contest_id = int(request.POST['contest_id'])
        problem_id = request.POST['problem_id'].strip()

    rb_integrated = 'rb_integrated' in request.POST and task_type not in simple_task_types
    one_file_upload = 'one_file_upload' in request.POST and rb_integrated
    accepted_after_contest_ok = 'accepted_after_contest_ok' in request.POST

    hidden_task = 'hidden_task' in request.POST
    task_text = request.POST.get('task_text', '').strip()

    return {'attrs': {
        'updated_by': user,
        'title': task_title,
        'short_title': task_short_title,
        'score_max': max_score,
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
        'task_text': task_text
        },
        'children': children,
        'groups': task_groups
    }


def task_create_or_edit(request, course, task_id=None):
    params = get_task_params(request, course.issue_status_system.has_accepted_after_deadline())

    changed_score_after_deadline = False
    if task_id:
        task = get_object_or_404(Task, id=task_id)
        changed_score_after_deadline = task.score_after_deadline != params['attrs']['score_after_deadline']
    else:
        task = Task()
        task.course = course

    for attr_name, attr_value in params['attrs'].items():
        setattr(task, attr_name, attr_value)

    if task.parent_task:
        if task.parent_task.is_hidden:
            task.is_hidden = True
    task.save()

    for subtask in Task.objects.filter(parent_task=task):
        subtask.is_hidden = task.is_hidden
        subtask.save()

    children = params['children']
    for course_task in Task.objects.filter(course=course):
        if children and course_task.id in map(int, children):
            course_task.parent_task = task
            course_task.save()
        elif course_task.parent_task == task:
            course_task.parent_task = None
            course_task.save()

    task_groups = params['groups']
    task.groups = task_groups
    task.set_position_in_new_group(task_groups)

    if task_id and changed_score_after_deadline:
        student_ids = User.objects.filter(group__in=task_groups).values_list('id', flat=True)
        for student_id in student_ids:
            parent_issue, created = Issue.objects.get_or_create(task_id=task.parent_task.id, student_id=student_id)
            total_mark = sum(Issue.objects.filter(
                task=task,
                student_id=student_id,
                status_field__tag=IssueStatus.STATUS_ACCEPTED_AFTER_DEADLINE
            ).values_list('mark', flat=True))
            if task.score_after_deadline:
                parent_issue.mark += total_mark
            else:
                parent_issue.mark -= total_mark
            parent_issue.save()

    if task.type == task.TYPE_SEMINAR:
        student_ids = User.objects.filter(group__in=task_groups).values_list('id', flat=True)
        for student_id in student_ids:
            issue, created = Issue.objects.get_or_create(task_id=task.id, student_id=student_id)
            issue.set_status_seminar()
            issue.mark = sum(Issue.objects.filter(
                task__parent_task=task,
                student_id=student_id).filter(
                Q(status_field__tag=IssueStatus.STATUS_ACCEPTED) |
                Q(task__score_after_deadline=True, status_field__tag=IssueStatus.STATUS_ACCEPTED_AFTER_DEADLINE)
            ).values_list('mark', flat=True))
            issue.save()

    reversion.set_user(request.user)
    if task_id:
        reversion.set_comment("Edit task")
    else:
        reversion.set_comment("Create task")

    return HttpResponse(json.dumps({'page_title': task.title + ' | ' + course.name + ' | ' + str(course.year),
                                    'redirect_page': '/task/edit/' + str(task.id) if not task_id else None}),
                        content_type="application/json")


@login_required
def get_contest_problems(request):
    if request.method != 'POST':
        return HttpResponseForbidden()

    course = get_object_or_404(Course, id=request.POST['course_id'])

    if not course.user_can_edit_course(request.user):
        return HttpResponseForbidden()

    contest_id = request.POST['contest_id']
    is_error = False
    error = ''
    problems = []

    got_info, contest_info = get_contest_info(contest_id)
    if "You're not allowed to view this contest." in contest_info:
        return HttpResponse(json.dumps({'problems': problems,
                                        'is_error': True,
                                        'error': _(u"net_prav_na_kontest")}),
                            content_type="application/json")

    problem_req = requests.get(settings.CONTEST_API_URL + 'problems?contestId=' + str(contest_id),
                               headers={'Authorization': 'OAuth ' + settings.CONTEST_OAUTH})
    problem_req = problem_req.json()

    if 'error' in problem_req:
        is_error = True
        if 'IndexOutOfBoundsException' in problem_req['error']['name']:
            error = _(u'kontesta_ne_sushestvuet')
        else:
            error = _(u'oshibka_kontesta') + ' ' + problem_req['error']['message']
    else:
        problems = problem_req['result']['problems']

        contest_info_problems = contest_info['problems']
        contest_info_deadline = contest_info['endTime'] if 'endTime' in contest_info else None
        problems = problems + contest_info_problems + [{'deadline': contest_info_deadline}]

    return HttpResponse(json.dumps({'problems': problems,
                                    'is_error': is_error,
                                    'error': error}),
                        content_type="application/json")


def prettify_contest_task_text(task_text):
    return task_text \
        .replace('<table', '<table class="table table-sm"') \
        .replace('src="', 'src="https://contest.yandex.ru')


@login_required
def contest_task_import(request):
    if not request.method == 'POST':
        return HttpResponseForbidden()

    course_id = int(request.POST['course_id'])
    course = get_object_or_404(Course, id=course_id)

    contest_id = int(request.POST['contest_id_for_task'])

    tasks = []
    common_params = get_task_params(request, course.issue_status_system.has_accepted_after_deadline)

    got_info, contest_info = get_contest_info(contest_id)
    problem_req = FakeResponse()
    problem_req = requests.get(settings.CONTEST_API_URL + 'problems?contestId=' + str(contest_id),
                               headers={'Authorization': 'OAuth ' + settings.CONTEST_OAUTH})
    problems = []
    if 'result' in problem_req.json():
        problems = problem_req.json()['result']['problems']

    problems_with_score = {problem['id']: problem.get('score') for problem in problems}
    problems_with_end = {problem['id']: problem.get('end') for problem in problems}

    if got_info:
        if problems:
            sort_order = [problem['id'] for problem in problems]
            contest_info['problems'].sort(key=lambda x: sort_order.index(x['problemId']))
        contest_problems = dict(request.POST)['contest_problems[]']
        for problem in contest_info['problems']:
            if problem['problemId'] in contest_problems:
                current_params = common_params['attrs'].copy()
                current_params.update({
                    'title': problem['problemTitle'],
                    'task_text': current_params['task_text'] or prettify_contest_task_text(problem['statement']),
                    'short_title': current_params['short_title'] or problem['alias'],
                    'contest_integrated': True,
                    'contest_id': contest_id,
                    'problem_id': problem['alias']
                })

                if not current_params['score_max'] and problems_with_score:
                    current_params['score_max'] = problems_with_score[problem['problemId']] or 0

                if not current_params['deadline_time'] and problems_with_end:
                    deadline = problems_with_end[problem['problemId']]
                    if deadline:
                        current_params['deadline_time'] = datetime.datetime.strptime(deadline, '%Y-%m-%dT%H:%M')

                tasks.append(current_params)

    elif "You're not allowed to view this contest." in contest_info:
        return HttpResponse(json.dumps({'is_error': True,
                                        'error': _(u"net_prav_na_kontest")}),
                            content_type="application/json")
    else:
        return HttpResponseForbidden()

    if not course.user_can_edit_course(request.user):
        return HttpResponseForbidden()

    for task in tasks:
        real_task = Task()
        real_task.course = course
        for attr_name, attr_value in task.items():
            setattr(real_task, attr_name, attr_value)
        real_task.save()

        task_groups = common_params['groups']
        real_task.groups = task_groups
        real_task.set_position_in_new_group(task_groups)

        reversion.set_user(request.user)
        reversion.set_comment("Import task")

    return HttpResponse("OK")


def get_task_text_popup(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    context = {
        'task': task,
    }

    return render_to_response('task_text_popup.html', context, context_instance=RequestContext(request))
