# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response, get_object_or_404, redirect
from tasks.models import Task
from courses.models import Course
from groups.models import Group
from issues.models import Issue
from issues.model_issue_status import IssueStatus
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
import requests
import reversion

import json


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
        return task_create_ot_edit(request, course)

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
        return task_create_ot_edit(request, task.course, task_id)

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


def task_create_ot_edit(request, course, task_id=None):
    user = request.user
    task_title = request.POST['task_title'].strip()
    task_short_title = request.POST['task_short_title'].strip() if 'task_short_title' in request.POST else task_title

    if 'max_score' in request.POST:
        max_score = request.POST['max_score']
        if max_score:
            max_score = int(max_score)
        else:
            max_score = 0
    else:
        max_score = 0

    task_groups = Group.objects.filter(id__in=dict(request.POST)['task_group_id[]'])

    parent_id = request.POST['parent_id']
    if not parent_id or parent_id == 'null':
        parent_id = None
    else:
        parent_id = int(parent_id)
    parent = None
    if parent_id is not None:
        parent = get_object_or_404(Task, id = parent_id)

    children = None
    if 'children[]' in request.POST:
        children = request.POST.getlist('children[]')
        if not children or children == 'null':
            children = None
        else:
            children = children

    if 'deadline' in request.POST:
        task_deadline = request.POST['deadline']
        if task_deadline:
            task_deadline = datetime.datetime.strptime(task_deadline, '%d-%m-%Y %H:%M')
        else:
            task_deadline = None
    else:
        task_deadline = None
    changed_task = False
    if 'changed_task' in request.POST:
        changed_task = True

    task_type = request.POST['task_type'].strip()

    contest_integrated = False
    contest_id = 0
    problem_id = None
    simple_task_types = [Task().TYPE_SIMPLE, Task().TYPE_MATERIAL]
    if 'contest_integrated' in request.POST and task_type not in simple_task_types:
        contest_integrated = True
        contest_id = int(request.POST['contest_id'])
        problem_id = request.POST['problem_id'].strip()

    rb_integrated = False
    if 'rb_integrated' in request.POST and task_type not in simple_task_types:
        rb_integrated = True

    one_file_upload = False
    if 'one_file_upload' in request.POST and rb_integrated:
        one_file_upload = True

    accepted_after_contest_ok = False
    if 'accepted_after_contest_ok' in request.POST and contest_integrated:
        accepted_after_contest_ok = True

    hidden_task = False
    if 'hidden_task' in request.POST:
        hidden_task = True

    task_text = request.POST['task_text'].strip()


    if task_id:
        task = get_object_or_404(Task, id=task_id)
    else:
        task = Task()
        task.course = course

    task.title = task_title
    task.short_title = task_short_title
    task.score_max = max_score

    task.parent_task = parent

    task.deadline_time = task_deadline
    if changed_task:
        task.send_to_users = True
        task.sended_notify = False
    else:
        task.send_to_users = False

    if task_type in dict(task.TASK_TYPE_CHOICES):
        task.type = task_type
    else:
        task.type = task.TYPE_FULL

    task.contest_integrated = contest_integrated
    if contest_integrated:
        task.contest_id = contest_id
        task.problem_id = problem_id

    task.rb_integrated = rb_integrated

    task.one_file_upload = one_file_upload

    task.accepted_after_contest_ok = accepted_after_contest_ok

    task.is_hidden = hidden_task

    for course_task in Task.objects.filter(course=course):
        if children and course_task.id in map(int, children):
            course_task.parent_task = task
            course_task.save()
        elif course_task.parent_task == task:
            course_task.parent_task = None
            course_task.save()

    if task.parent_task:
        if task.parent_task.is_hidden:
            task.is_hidden = True
    for subtask in Task.objects.filter(parent_task=task):
        subtask.is_hidden = hidden_task
        subtask.save()

    task.task_text = task_text

    task.updated_by = user
    task.save()

    task.groups = task_groups
    task.set_position_in_new_group(task_groups)

    if task.type == task.TYPE_SEMINAR:
        students = User.objects.filter(group__in=task_groups).all()
        for student in students:
            issue, created = Issue.objects.get_or_create(task_id=task.id, student_id=student.id)
            issue.set_status_by_tag('seminar')
            issue.mark = sum([x.mark for x in Issue.objects.filter(task__parent_task=task, student_id=student.id).all()])
            issue.save()

    reversion.set_user(user)
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

    task_short_title = request.POST['task_short_title'].strip() if 'task_short_title' in request.POST else ''

    if 'max_score' in request.POST:
        max_score = int(request.POST['max_score'])
    else:
        max_score = None

    task_groups = Group.objects.filter(id__in=dict(request.POST)['task_group_id[]'])

    if 'deadline' in request.POST:
        task_deadline = request.POST['deadline']
        if task_deadline:
            task_deadline = datetime.datetime.strptime(task_deadline, '%d-%m-%Y %H:%M')
        else:
            task_deadline = None
    else:
        task_deadline = None

    changed_task = False
    if 'changed_task' in request.POST:
        changed_task = True

    rb_integrated = False
    if 'rb_integrated' in request.POST:
        rb_integrated = True

    one_file_upload = False
    if 'one_file_upload' in request.POST and rb_integrated:
        one_file_upload = True

    accepted_after_contest_ok = False
    if 'accepted_after_contest_ok' in request.POST:
        accepted_after_contest_ok = True

    hidden_task = False
    if 'hidden_task' in request.POST:
        hidden_task = True

    parent_id = request.POST['parent_id']
    if not parent_id or parent_id == 'null':
        parent_id = None
    else:
        parent_id = int(parent_id)
    parent = None
    if parent_id is not None:
        parent = get_object_or_404(Task, id = parent_id)

    if 'task_text' in request.POST:
        task_text = request.POST['task_text'].strip()
    else:
        task_text = ''

    tasks = []

    got_info, contest_info = get_contest_info(contest_id)
    problem_req = FakeResponse()
    problem_req = requests.get(settings.CONTEST_API_URL + 'problems?contestId=' + str(contest_id),
                               headers={'Authorization': 'OAuth ' + settings.CONTEST_OAUTH})
    problems = []
    if 'result' in problem_req.json():
        problems = problem_req.json()['result']['problems']

    problems_with_score = {problem['id']:problem['score'] if 'score' in problem else None for problem in problems}
    problems_with_end = {problem['id']:problem['end'] if 'end' in problem else None for problem in problems}

    if got_info:
        if problems:
            sort_order = [problem['id'] for problem in problems]
            contest_info['problems'].sort(key=lambda x: sort_order.index(x['problemId']))
        contest_problems = dict(request.POST)['contest_problems[]']
        for problem in contest_info['problems']:
            if problem['problemId'] in contest_problems:
                tasks.append({})
                tasks[-1]['task_title'] = problem['problemTitle']
                tasks[-1]['task_text'] = problem['statement']
                tasks[-1]['problem_id'] = problem['alias']
                if problems_with_score:
                    tasks[-1]['max_score'] = problems_with_score[problem['problemId']]
                else:
                    tasks[-1]['max_score'] = None
                if problems_with_end:
                    tasks[-1]['deadline_time'] = problems_with_end[problem['problemId']]
                else:
                    tasks[-1]['deadline_time'] = None

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
        real_task.parent_task = parent

        if changed_task:
            real_task.send_to_users = True
            real_task.sended_notify = False
        else:
            real_task.send_to_users = False

        if task_deadline:
            real_task.deadline_time = task_deadline
        elif task['deadline_time']:
            real_task.deadline_time = datetime.datetime.strptime(task['deadline_time'], '%Y-%m-%dT%H:%M')
        else:
            real_task.deadline_time = None

        real_task.title = task['task_title']
        real_task.short_title = task_short_title if task_short_title else task['problem_id']

        if task_text:
            real_task.task_text = task_text
        elif task['task_text']:
            real_task.task_text = prettify_contest_task_text(task['task_text'])
        else:
            real_task.task_text = ''

        if max_score:
            real_task.score_max = max_score
        elif task['max_score']:
            real_task.score_max = task['max_score']
        else:
            real_task.score_max = 0

        real_task.contest_integrated = True
        real_task.contest_id = contest_id
        real_task.problem_id = task['problem_id']

        real_task.rb_integrated = rb_integrated

        real_task.one_file_upload = one_file_upload

        real_task.accepted_after_contest_ok = accepted_after_contest_ok

        real_task.is_hidden = hidden_task
        real_task.updated_by = request.user
        real_task.save()

        real_task.groups = task_groups
        real_task.set_position_in_new_group(task_groups)

        reversion.set_user(request.user)
        reversion.set_comment("Import task")

    return HttpResponse("OK")


def get_task_text_popup(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    context = {
        'task' : task,
    }

    return render_to_response('task_text_popup.html', context, context_instance=RequestContext(request))


def update_status_check(request, redirect=True):
    if request.method == "POST":
        try:
            student_id = int(request.POST['student_id'])
            task_id = int(request.POST['task_id'])
            task = Task.objects.get(id=task_id)
            student = User.objects.get(id=student_id)
            task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)
            new_status = request.POST['new_status']
            if task_taken.user_can_change_status(request.user, new_status):
                task_taken.status_check = new_status
                task_taken.save()
        except ObjectDoesNotExist:
            pass
        if redirect:
            return HttpResponseRedirect(reverse('courses.views.tasks_list', kwargs={'course_id':task_taken.task.course.id}))
    else:
        return HttpResponseForbidden()


def ajax_get_review_data(request, task_id, student_id):
    if not request.is_ajax():
        return HttpResponseForbidden()

    id_issue_gr_review = ""
    pdf_link = ""
    gr_review_update_time = ""
    pdf_update_time = ""

    try:
        task = Task.objects.get(id=task_id)
        student = User.objects.get(id=student_id)
        task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)

        if task_taken.id_issue_gr_review:
            id_issue_gr_review = task_taken.id_issue_gr_review
            gr_review_update_time = task_taken.gr_review_update_time.strftime('%d/%m/%Y %H:%M')

        if task_taken.pdf:
            pdf_link = task_taken.pdf.url
            pdf_update_time = task_taken.pdf_update_time.strftime('%d/%m/%Y %H:%M')

    except ObjectDoesNotExist:
        pass

    review_data = {
        'id_issue_gr_review' : id_issue_gr_review,
        'pdf_link' : pdf_link,
        'gr_review_update_time' : gr_review_update_time,
        'pdf_update_time' : pdf_update_time,
    }
    return HttpResponse(json.dumps(review_data), content_type="application/json")

def ajax_predict_status(request, task_id, student_id, score):
    if not request.is_ajax():
        return HttpResponseForbidden()

    predicted_status = ""

    try:
        score = float(score)
        task = Task.objects.get(id=task_id)
        student = User.objects.get(id=student_id)

        task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)

        eps = 10**(-5)
        if abs(score - task.score_max) < eps:
            predicted_status = TaskTaken.OK
        elif abs(score - task_taken.score) > eps:
            predicted_status = TaskTaken.EDIT
        else:
            predicted_status = task_taken.status_check

    except ObjectDoesNotExist:
        pass

    data = {
        'predicted_status' : predicted_status,
    }

    return HttpResponse(json.dumps(data), content_type="application/json")

def ajax_get_status_check(request, task_id, student_id):
    if not request.is_ajax():
        return HttpResponseForbidden()

    current_status = ""
    choices_status = []
    is_possible_status = []

    try:
        task = Task.objects.get(id=task_id)
        student = User.objects.get(id=student_id)

        task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)
        choices_status = TaskTaken.STATUS_CHECK_CHOICES
        is_possible_status = [task_taken.user_can_change_status(request.user, status[0]) for status in choices_status]

        current_status = task_taken.status_check

        for status in choices_status:
            if status[0] == current_status:
                current_status = status
                break

        is_possible_status = is_possible_status

    except ObjectDoesNotExist:
        pass

    status_check_data = {
        'current_status' : current_status,
        'choices_status' : choices_status,
        'is_possible_status' : is_possible_status,
    }

    return HttpResponse(json.dumps(status_check_data), content_type="application/json")


def ajax_get_teacher(request, task_id, student_id):
    if not request.is_ajax():
        return HttpResponseForbidden()

    teacher_name = ""
    try:
        task = Task.objects.get(id=task_id)
        student = User.objects.get(id=student_id)
        task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)
        if task_taken.teacher:
            teacher_name = task_taken.teacher.get_full_name()
    except ObjectDoesNotExist:
        pass

    data = {
        'teacher_name' : teacher_name
    }

    return HttpResponse(json.dumps(data), content_type="application/json")


def ajax_set_teacher(request, task_id, student_id, teacher_id):
    if not request.is_ajax():
        return HttpResponseForbidden()

    try:
        task = Task.objects.get(id=task_id)
        student = User.objects.get(id=student_id)
        teacher = User.objects.get(id=teacher_id)
        task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)
        if (task_taken.user_can_change_teacher(request.user)):
            task_taken.teacher = teacher
            task_taken.save()
    except ObjectDoesNotExist:
        pass

    return HttpResponse({}, content_type="application/json")


def ajax_delete_teacher(request, task_id, student_id):
    if not request.is_ajax():
        return HttpResponseForbidden()

    try:
        task = Task.objects.get(id=task_id)
        student = User.objects.get(id=student_id)
        task_taken, created = TaskTaken.objects.get_or_create(user=student, task=task)
        if task_taken.user_can_change_teacher(request.user):
            task_taken.teacher = None
            task_taken.save()
    except ObjectDoesNotExist:
        pass

    return HttpResponse({}, content_type="application/json")
