#coding: utf-8
import pprint

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.conf import settings

import datetime
import pysvn
import urllib, urllib2
import httplib

from courses.models import Course
from groups.models import Group
from tasks.models import TaskTaken, Task
from tasks.views import update_status_check
from years.models import Year
from years.common import get_current_year
from course_statistics import CourseStatistics
from score import TaskInfo
from anysvn.common import svn_log_rev_message, svn_log_head_revision, get_svn_external_url, svn_log_min_revision
from anyrb.common import AnyRB
from issues.models import Issue

from common.ordered_dict import OrderedDict

from courses.forms import PdfForm, QueueForm
from django.utils.html import strip_tags
from filemanager import FileManager
from settings import UPLOAD_ROOT
import os.path

import json

@login_required
def filemanager(request, path, course_id):
    course = get_object_or_404(Course, id=course_id)
    if course.user_is_teacher(request.user):
        course_folder = UPLOAD_ROOT + "/" + course.name
        if os.path.exists(course_folder):
            fm = FileManager(course_folder)
        else:
            os.mkdir(course_folder)
            fm = FileManager(course_folder)
        return fm.render(request,path)
    else:
        return HttpResponseForbidden()

@login_required
def queue_page(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if not course.user_can_see_queue(request.user):
        return HttpResponseForbidden()

    issues = Issue.objects.filter(task__course=course).exclude(status=Issue.STATUS_NEW).exclude(status=Issue.STATUS_ACCEPTED)

    context = dict()
    if request.method == 'POST':
        queue_form = QueueForm(request.POST)
        if queue_form.is_valid():
            cd = queue_form.cleaned_data
            if not cd['mine']:
                issues = issues.exclude(responsible=request.user)
            if not cd['not_mine']:
                issues = issues.filter(Q(responsible=request.user) | Q(responsible__isnull=True))
            if not cd['following']:
                issues = issues.exclude(followers=request.user)
            if not cd['not_owned']:
                issues = issues.exclude(responsible__isnull=True)
            if not cd['rework']:
                issues = issues.exclude(status=Issue.STATUS_REWORK)
            if not cd['verefication']:
                issues = issues.exclude(status=Issue.STATUS_VERIFICATION)

            now_date = datetime.datetime.now()
            delta = datetime.timedelta(days=cd['overdue'])
            filter_date = now_date - delta
            issues = issues.filter(update_time__lte=filter_date)
    else:
        queue_form = QueueForm()
        issues = issues.exclude(status=Issue.STATUS_REWORK) # not good

    issues = issues.order_by('update_time')
    context['course'] = course
    context['issues'] = issues
    context['queue_form'] = queue_form
    return render_to_response('courses/queue.html', context, context_instance=RequestContext(request))

@login_required
def course_page(request, course_id):
    """Page with course related information
    contexts:
        - tasklist
        - tasks_description
    """

    course = get_object_or_404(Course, id=course_id)

    if course.private and not course.user_is_attended(request.user):
        return render_to_response('course_private_forbidden.html', {"course" : course}, context_instance=RequestContext(request))

    tasklist_context = get_tasklist_context(request, course)
    context = tasklist_context
    context['tasklist_template'] = 'courses/tasklist/shad_cpp.html'

    return render_to_response('courses/course.html', context, context_instance=RequestContext(request))


def tasklist_shad_cpp(request, course):

    user = request.user
    user_is_attended = False
    user_is_attended_special_course = False

    course.can_edit = course.user_can_edit_course(user)
    if course.can_be_chosen_by_extern:
        course.groups.add(course.group_with_extern)

    group_x_student_x_task_takens = OrderedDict()
    group_x_task_list = {}
    group_x_max_score = {}

    task = Task()
    task.is_shown = None
    task.is_hidden = None
    
    for group in course.groups.all().order_by('name'):
        student_x_task_x_task_takens = {}

        group_x_task_list[group] = Task.objects.filter(course=course).filter(group=group).order_by('weight')
        group_x_max_score.setdefault(group, 0)

        for task in group_x_task_list[group]:
            task.add_user_properties(user)

            if not task.is_hidden:
                group_x_max_score[group] += task.score_max
            if task.task_text is None:
                task.task_text = ''

        issues_students_in_group = Issue.objects.filter(task__in=group_x_task_list[group]).filter(student__group__in=[group]).order_by('student')

        from collections import defaultdict
        issues_x_student = defaultdict(list)
        for issue in issues_students_in_group.all():
            student_id = issue.student.id
            issues_x_student[student_id].append(issue)

        for student in group.students.filter(is_active=True):
            if user == student:
                user_is_attended = True
                user_is_attended_special_course = True

            task_list = group_x_task_list[group]

            student_task_takens = issues_x_student[student.id]

            task_x_task_taken = {}
            student_summ_scores = 0
            for task_taken in student_task_takens:
                task_x_task_taken[task_taken.task.id] = task_taken
                if not task_taken.task.is_hidden:
                    student_summ_scores += task_taken.score()

            student_x_task_x_task_takens[student] = (task_x_task_taken, student_summ_scores)

        group_x_student_x_task_takens[group] = student_x_task_x_task_takens

    group_x_student_information = OrderedDict()
    for group,student_x_task_x_task_takens in group_x_student_x_task_takens.iteritems():
        group_x_student_information.setdefault(group, [])

        for student in sorted(student_x_task_x_task_takens.keys(), key=lambda x: u"{0} {1}".format(x.last_name, x.first_name)):
            if user == student:
                user_is_attended = True
            elif not course.user_can_see_transcript(user, student):
                continue

            group_x_student_information[group].append((student, student_x_task_x_task_takens[student][0], student_x_task_x_task_takens[student][1]))


    extern_max_score = 0
    extern_student_x_task_takens = {}

    extern_tasks = Task.objects.filter(course=course).filter(group=None).order_by('weight')
    for task in extern_tasks:
        task.add_user_properties(user)

        if not task.is_hidden:
            extern_max_score += task.score_max
        if task.task_text is None:
            task.task_text = ''


    task_takens = TaskTaken.objects.filter(task__in=extern_tasks)
    for student in course.students.all():
        if user == student:
            user_is_attended = True
            user_is_attended_special_course = True
        elif not course.user_can_see_transcript(user, student):
            continue

        task_x_task_taken = {}

        student_summ_scores = 0
        student_task_takens = filter(lambda x: x.user == student, task_takens)

        for task_taken in student_task_takens:
            task_x_task_taken[task_taken.task.id] = task_taken
            if not task_taken.task.is_hidden:
                student_summ_scores += task_taken.score

        extern_student_x_task_takens[student] = (task_x_task_taken, student_summ_scores)

    extern_student_information = []
    for student in sorted(extern_student_x_task_takens.keys(), key=lambda x: u"{0} {1}".format(x.last_name, x.first_name)):
        if user == student:
            user_is_attended = True

        extern_student_information.append((student, extern_student_x_task_takens[student][0], extern_student_x_task_takens[student][1]))

    context = {
        'course'        : course,
        'group_information'   : group_x_student_information,
        'group_tasks'   : group_x_task_list,
        'group_x_max_score' : group_x_max_score,

        'extern_max_score' : extern_max_score,
        'extern_tasks'  : extern_tasks,
        'extern_student_information' : extern_student_information,

        'user' : user,
        'user_is_attended' : user_is_attended,
        'user_is_attended_special_course' : user_is_attended_special_course,
        'user_is_teacher': course.user_is_teacher(user),
        
        'visible_queue' : course.user_can_see_queue(user),
    }

    return context


def get_tasklist_context(request, course):
    if course.type == Course.TYPE_SHAD_CPP:
        return tasklist_shad_cpp(request, course)
    return


def tasks_list(request, course_id, get_context=False):
    course = get_object_or_404(Course, id=course_id)

    if course.private and not course.user_is_attended(request.user):
        return render_to_response('course_private_forbidden.html', {"course" : course}, context_instance=RequestContext(request))

    if course.type == Course.TYPE_POTOK:
        return tasks_list_potok(request, course)

    if course.type == Course.TYPE_ONE_TASK_MANY_GROUP:
        return tasks_list_one_tasks_many_group(request, course)

    if course.type == Course.TYPE_MANY_TASK_MANY_GROUP:
        if get_context:
            return tasks_list_many_task_many_group(request, course, get_context=True);
        return tasks_list_many_task_many_group(request, course)

    if course.type == Course.TYPE_SPECIAL_COURSE:
        if course.take_policy == Course.TAKE_POLICY_SELF_TAKEN:
            return tasks_list_potok(request, course)
        if course.take_policy == Course.TAKE_POLICY_ALL_TASKS_TO_ALL_STUDENTS:
            return tasks_list_many_task_many_group(request, course)

    return


def _group_task_takens_by_task(task_takens):
    task_x_task_takens = {}
    for task_taken in task_takens:
        task = task_taken.task

        task_x_task_takens.setdefault(task, [])
        task_x_task_takens[task].append(task_taken)

    return task_x_task_takens


def tasks_list_one_tasks_many_group(request, course):
    user = request.user
    user_is_attended = False
    user_is_attended_special_course = False
    course.can_edit = course.user_can_edit_course(user)
    students_x_tasks = OrderedDict()
    tasks = list(Task.objects.filter(course=course).order_by('weight'))
    students = []
    for group in course.groups.all().order_by('name'):
        for student in group.students.filter(is_active=True):
            if student == user:
                user_is_attended = True
            elif not course.user_can_see_transcript(user, student):
                continue
            student.group_for_this_course = group
            students.append(student)

    user_is_attended = user in students

    for student in course.students.all():
        if course.user_can_see_transcript(user, student):
            students.extend([student])

    if not user_is_attended and user in students:
        user_is_attended = True
        user_is_attended_special_course = True

    students = sorted(students, key=lambda x:(x.last_name, x.first_name))

    score_max = 0
    for task in tasks:
        score_max += task.score_max
        task.add_user_properties(user)

    for student in students:
        student_task_takens = TaskTaken.objects.filter(task__in=tasks).filter(user=student)
        task_x_task_takens = _group_task_takens_by_task(student_task_takens)

        students_x_tasks.setdefault(student, OrderedDict())
        score_sum = 0
        for task in tasks:
            task_taken = task_x_task_takens.get(task, [TaskTaken()])[0]
            score_sum += task_taken.score
            students_x_tasks[student][task] = task_taken
        student.score_sum = score_sum

    context = {
        'tasks' : tasks,
        'students_x_tasks' : students_x_tasks,
        'score_max' : score_max,

        'course' : course,
        'user_is_attended' : user_is_attended,
        'user_is_attended_special_course' : user_is_attended_special_course,
    }

    return render_to_response('course_tasks_one_tasks_many_group.html', context, context_instance=RequestContext(request))


def tasks_list_many_task_many_group(request, course, get_context=False):
    user = request.user
    user_is_attended = False
    user_is_attended_special_course = False

    course.can_edit = course.user_can_edit_course(user)

    group_x_student_x_task_takens = OrderedDict()
    group_x_task_list = {}
    group_x_max_score = {}

    task = Task()
    task.is_shown = None
    task.is_hidden = None

    for group in course.groups.all().order_by('name'):
        student_x_task_x_task_takens = {}

        group_x_task_list[group] = Task.objects.filter(course=course).filter(group=group).order_by('weight')
        group_x_max_score.setdefault(group, 0)

        for task in group_x_task_list[group]:
            task.add_user_properties(user)

            if not task.is_hidden:
                group_x_max_score[group] += task.score_max
            if task.task_text is None:
                task.task_text = ''

        for student in group.students.filter(is_active=True):
            if user == student:
                user_is_attended = True

            task_list = group_x_task_list[group]

            student_task_takens = TaskTaken.objects.filter(task__in=group_x_task_list[group]).filter(user=student)

            task_x_task_taken = {}
            student_summ_scores = 0
            for task_taken in student_task_takens:
                task_x_task_taken[task_taken.task.id] = task_taken
                if not task_taken.task.is_hidden:
                    student_summ_scores += task_taken.score

            student_x_task_x_task_takens[student] = (task_x_task_taken, student_summ_scores)

        group_x_student_x_task_takens[group] = student_x_task_x_task_takens

    group_x_student_information = OrderedDict()
    for group,student_x_task_x_task_takens in group_x_student_x_task_takens.iteritems():
        group_x_student_information.setdefault(group, [])

        for student in sorted(student_x_task_x_task_takens.keys(), key=lambda x: u"{0} {1}".format(x.last_name, x.first_name)):
            if user == student:
                user_is_attended = True
            elif not course.user_can_see_transcript(user, student):
                continue

            group_x_student_information[group].append((student, student_x_task_x_task_takens[student][0], student_x_task_x_task_takens[student][1]))


    extern_max_score = 0
    extern_student_x_task_takens = {}

    extern_tasks = Task.objects.filter(course=course).filter(group=None).order_by('weight')
    for task in extern_tasks:
        task.add_user_properties(user)

        if not task.is_hidden:
            extern_max_score += task.score_max
        if task.task_text is None:
            task.task_text = ''


    task_takens = TaskTaken.objects.filter(task__in=extern_tasks)
    for student in course.students.all():
        if user == student:
            user_is_attended = True
            user_is_attended_special_course = True
        elif not course.user_can_see_transcript(user, student):
            continue

        task_x_task_taken = {}

        student_summ_scores = 0
        student_task_takens = filter(lambda x: x.user == student, task_takens)

        for task_taken in student_task_takens:
            task_x_task_taken[task_taken.task.id] = task_taken
            if not task_taken.task.is_hidden:
                student_summ_scores += task_taken.score

        extern_student_x_task_takens[student] = (task_x_task_taken, student_summ_scores)

    extern_student_information = []
    for student in sorted(extern_student_x_task_takens.keys(), key=lambda x: u"{0} {1}".format(x.last_name, x.first_name)):
        if user == student:
            user_is_attended = True

        extern_student_information.append((student, extern_student_x_task_takens[student][0], extern_student_x_task_takens[student][1]))

    context = {
        'course'        : course,
        'group_information'   : group_x_student_information,
        'group_tasks'   : group_x_task_list,
        'group_x_max_score' : group_x_max_score,

        'extern_max_score' : extern_max_score,
        'extern_tasks'  : extern_tasks,
        'extern_student_information' : extern_student_information,

        'user' : user,
        'user_is_attended' : user_is_attended,
        'user_is_attended_special_course' : user_is_attended_special_course,

        'visible_queue' : course.user_can_see_queue(user),
    }

    if get_context:
        return context
    else:
        return render_to_response('courses/course_page.html', context, context_instance=RequestContext(request))


def tasks_list_potok(request, course):
    user = request.user

    course.can_edit = course.user_can_edit_course(user)
    delta = datetime.timedelta(days=course.max_days_without_score)
    task_and_task_taken = []
    for task in Task.objects.filter(course=course).filter(parent_task=None).order_by('weight'):
        task.add_user_properties(user)

        if task.task_text is None:
            task.task_text = ''

        task_taken_list = []
        for task_taken in TaskTaken.objects.filter(task=task).exclude(task__is_hidden=True).filter(Q( Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED))):
            if not course.user_can_see_transcript(user, task_taken.user):
                continue
            if task_taken.status == TaskTaken.STATUS_TAKEN:
                task_taken.cancel_date = task_taken.added_time + delta
            task_taken_list.append(task_taken)

        if task.has_subtasks():
            subtask_and_task_takens = []
            for subtask in Task.objects.filter(parent_task=task).order_by('weight'):
                subtask.add_user_properties(user)

                if subtask.task_text is None:
                    subtask.task_text = ''

                subtask_takens = list()
                for subtask_taken in TaskTaken.objects.filter(task=subtask).exclude(task__is_hidden=True).exclude(task__parent_task__is_hidden=True).filter(Q( Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED))):
                    if course.user_can_see_transcript(user, task_taken.user):
                        subtask_takens.append(subtask_taken)
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

def get_task(request, course_id, task_id):
    user = request.user

    task = get_object_or_404(Task, id=task_id)
    user_can_take_task, reason = task.user_can_take_task(user)
    if user_can_take_task:
        task_taken, _ = TaskTaken.objects.get_or_create(user=user, task=task)
        task_taken.status = TaskTaken.STATUS_TAKEN
        task_taken.save()

    return redirect(tasks_list, course_id=course_id)

def cancel_task(request, course_id, task_id):
    user = request.user

    task = get_object_or_404(Task, id=task_id)

    if task.user_can_cancel_task(user):
        task_taken = get_object_or_404(TaskTaken, user=user, task=task)
        task_taken.status = TaskTaken.STATUS_CANCELLED
        task_taken.save()

    return redirect(tasks_list, course_id=course_id)

def score_task(request):
    update_status_check(request, False)

    user = request.user

    if not request.method == 'POST':
        return HttpResponseForbidden()

    for key in ['task_id', 'student_id', 'score', 'comment']:
        if key not in request.POST:
            return HttpResponseForbidden()

    if not request.POST['score']:
        return HttpResponse("OK")

    try:
        task_id = int(request.POST['task_id'])
        student_id = int(request.POST['student_id'])
        score = float(request.POST['score'])
        comment = request.POST['comment'].strip()
    except ValueError: #not int
        return HttpResponseForbidden()

    task = get_object_or_404(Task, id = task_id)

    if not task.user_can_score_task(user):
        return HttpResponseForbidden()

    student = get_object_or_404(User, id = student_id)
    task_taken, _ = TaskTaken.objects.get_or_create(user = student, task = task)


    task_taken.status = TaskTaken.STATUS_SCORED
    task_taken.score = score
    task_taken.scored_by = user
    if comment:
        if task_taken.teacher_comments is None:
            task_taken.teacher_comments = ''

        task_taken.teacher_comments += u"\n{0} Оценка: {1} {2}:\n{3}".format(datetime.datetime.now().strftime('%d.%m.%Y'), score, user.get_full_name(), comment);
    task_taken.save()

    return HttpResponse("OK")

def edit_task(request):
    user = request.user

    if not request.method == 'POST':
        return HttpResponseForbidden()

    for key in ['task_id', 'task_title', 'task_text',
                'max_score', 'contest_id', 'problem_id']:
        if key not in request.POST:
            return HttpResponseForbidden()

    hidden_task = False
    if 'hidden_task' in request.POST:
        hidden_task = True

    try:
        task_id = int(request.POST['task_id'])
        task_title = request.POST['task_title'].strip()
        task_text = request.POST['task_text'].strip()
        max_score = int(request.POST['max_score'])
        contest_id = int(request.POST['contest_id'])
        problem_id = request.POST['problem_id'].strip()
    except ValueError: #not int
        return HttpResponseForbidden()

    task = get_object_or_404(Task, id = task_id)

    if not task.course.user_is_teacher(user):
        return HttpResponseForbidden()

    task.is_hidden = hidden_task
    if task.parent_task:
        if task.parent_task.is_hidden:
            task.is_hidden = True

    task.title = task_title
    task.task_text = task_text
    task.score_max = max_score
    task.contest_id = contest_id
    task.problem_id = problem_id
    task.updated_by = user
    task.save()

    for subtask in Task.objects.filter(parent_task=task):
        subtask.is_hidden = hidden_task
        subtask.save()

    return HttpResponse("OK")

def add_task(request):
    user = request.user

    if not request.method == 'POST':
        return HttpResponseForbidden()

    for key in ['course_id', 'group_id', 'parent_id', 'task_title',
                'task_text','max_score', 'contest_id', 'problem_id']:
        if key not in request.POST:
            return HttpResponseForbidden()

    hidden_task = False
    if 'hidden_task' in request.POST:
        hidden_task = True

    try:
        course_id = int(request.POST['course_id'])
        task_title = request.POST['task_title'].strip()
        task_text = request.POST['task_text'].strip()
        max_score = int(request.POST['max_score'])
        contest_id = int(request.POST['contest_id'])
        problem_id = request.POST['problem_id'].strip()

        group_id = request.POST['group_id']
        if not group_id or group_id == 'null':
            group_id = None
        else:
            group_id = int(group_id)

        parent_id = request.POST['parent_id']
        if not parent_id or parent_id == 'null':
            parent_id = None
        else:
            parent_id = int(parent_id)

    except ValueError: #not int
        return HttpResponseForbidden()

    course = get_object_or_404(Course, id = course_id)
    group = None
    if group_id is not None:
        group = get_object_or_404(Group, id = group_id)
    parent = None
    if parent_id is not None:
        parent = get_object_or_404(Task, id = parent_id)

    if not course.user_can_edit_course(user):
        return HttpResponseForbidden()

    max_weight_query = Task.objects.filter(course=course)
    if group:
        max_weight_query = max_weight_query.filter(group=group)
    if parent:
        max_weight_query = max_weight_query.filter(parent_task=parent)

    tasks = max_weight_query.aggregate(Max('weight'))
    _, max_weight = tasks.items()[0]
    if max_weight is None:
        max_weight = 0
    max_weight += 1

    task = Task()
    task.course = course
    task.group = group
    task.parent_task = parent
    task.weight = max_weight
    task.title = task_title
    task.task_text = task_text
    task.score_max = max_score
    task.contest_id = contest_id
    task.problem_id = problem_id
    task.is_hidden = hidden_task
    task.updated_by = user
    task.save()

    return HttpResponse("OK")

def courses_list(request, year=None):
    if year is None:
        year_object = get_current_year()
    else:
        year_object = get_object_or_404(Year, start_year=year)

    if year_object is None:
        raise Http404

    courses_list = Course.objects.filter(year=year_object).order_by('name')

    context = {
        'courses_list'  : courses_list,
        'year'  : year_object,
    }

    return render_to_response('course_list.html', context, context_instance=RequestContext(request))


def course_statistics(request, course_id):
    course = get_object_or_404(Course, id = course_id)
    course_tasks = Task.objects.filter(course=course).exclude(is_hidden=True)

    statistics = CourseStatistics(course_tasks)

    for group in course.groups.all().order_by('name'):
        statistics.update(group)

    context = {
        'course'            : course,
        'groups_statistics'  : statistics.get_groups_statistics(),
        'course_statistics' : statistics.get_course_statistics(),
    }

    return render_to_response('statistics.html', context, context_instance=RequestContext(request))

def tasks_description(request, course, get_context=False):

    group_x_tasks = {}
    course_tasks = []
    if course.type == Course.TYPE_MANY_TASK_MANY_GROUP:
        for group in course.groups.all():
            group_x_tasks[group] = Task.objects.filter(course=course).filter(group=group).exclude(is_hidden=True).order_by('weight')

        course_tasks = Task.objects.filter(course=course).filter(group=None).exclude(is_hidden=True).order_by('weight')
    else:
        course_tasks = Task.objects.filter(course=course).exclude(is_hidden=True).order_by('weight')

    context = {
        'course'            : course,
        'group_x_tasks'     : group_x_tasks,
        'course_tasks'      : course_tasks,
        'visible_queue'     : course.user_can_see_queue(request.user),
    }

    if get_context:
        return context

    return render_to_response('course_tasks_description.html', context, context_instance=RequestContext(request))

def edit_course_information(request):
    user = request.user

    if not request.method == 'POST':
        return HttpResponseForbidden()

    for key in ['course_id', 'course_information']:
        if key not in request.POST:
            return HttpResponseForbidden()

    try:
        course_id = int(request.POST['course_id'])
        course_information = request.POST['course_information'].strip()
    except ValueError: #not int
        return HttpResponseForbidden()

    course = get_object_or_404(Course, id = course_id)

    if not course.user_can_edit_course(user):
        return HttpResponseForbidden()

    course.information = course_information
    course.save()

    return HttpResponse("OK")

@login_required
def set_spectial_course_attend(request):
    user = request.user
    if not request.method == 'POST':
        return HttpResponseForbidden()

    try:
        course_id = int(request.POST['course_id'])
        action = request.POST['action']
    except ValueError: #not int
        return HttpResponseForbidden()

    course = get_object_or_404(Course, id=course_id)

    if action == "add":
        course.add_user_to_group_with_extern(user)

    if action == "remove":
        course.remove_user_from_group_with_extern(user)

    return HttpResponse("OK")

class SubmitReview(View):
    @method_decorator(login_required)
    def dispatch(self, request, task_id, *args, **kwargs):
        user = request.user
        task = get_object_or_404(Task, id=task_id)

        if not task.user_can_pass_task(user):
            return HttpResponseForbidden()

        pdf_form = PdfForm()

        can_send_task_to_teacher = False

        pdf_info = ""
        id_issue_gr_review = ""

        if len(TaskTaken.objects.filter(task=task, user=user)) > 0:
            task_taken = TaskTaken.objects.get(task=task, user=user)
            if task_taken.id_issue_gr_review:
                id_issue_gr_review = task_taken.id_issue_gr_review
            if task_taken.pdf:
                pdf_info = { "url":task_taken.pdf.url, "name":task_taken.pdf.name}
            if task_taken.status_check == TaskTaken.EDIT:
                can_send_task_to_teacher = True

        context = {
            "task" : task,
            "pdf_form": pdf_form,
            "gr_error": request.GET.get('gr_error', ''),
            "pdf_error": request.GET.get('pdf_error', ''),
            "can_send_task_to_teacher": can_send_task_to_teacher,
            "id_issue_gr_review" : id_issue_gr_review,
            "pdf_info" : pdf_info,
        }

        return render_to_response('submit_review.html', context, context_instance=RequestContext(request))

class SubmitReviewForm(View):

    def _get_description(self, request, task, svn_path, rev_a=None, rev_b=None):
        user = request.user

        descriptions = []
        descriptions.append("SVN: {0}".format(get_svn_external_url(user, svn_path)))
        descriptions.append("")
        descriptions.append("SVN Log:")
        for log in svn_log_rev_message(user, svn_path):
            rev = log[0]
            if (not rev_a or rev >= rev_a) and (not rev_b or rev <= rev_b):
                descriptions.append("{0:3} {1:20} {2} {3}".format(*log))

        return "\n".join(descriptions)


    def _submit_review(self, request, task, svn_path):
        user = request.user

        try:
            rev_a = int(request.POST.get('rev_a'))
            rev_b = int(request.POST.get('rev_b'))
        except TypeError: #not int
            return HttpResponseForbidden()
        except ValueError: #not int
            return HttpResponseForbidden()

        if rev_a == rev_b:
            return HttpResponseForbidden()

        if rev_b < rev_a:
            rev_a, rev_b = rev_b, rev_a

        review_id = None
        try:
            issue = Issue.objects.filter(task=task, student=user).order_by('-update_time')[0]
            review_id = issue.rb_review_id
        except Issue.DoesNotExist:
            pass
        except IndexError:
            pass

        issue = Issue()
        issue.task = task
        issue.student = user
        issue.svn_commit_id = rev_b

        summary = u"[{0}][{1}] {2}".format(user.get_full_name(), task.course.get_user_group(user), task.title)

        review_group_name = settings.RB_API_DEFAULT_REVIEW_GROUP
        if task.course.name_id:
            review_group_name =  "teachers_{0}".format(task.course.name_id)
        else:
            try:
                review_group_name = "teachers_{0}".format(task.course.name)
            except Exception:
                pass

        review_group_name = review_group_name.replace(".", "_")
        review_group_name = review_group_name.replace("/", "_")
        review_group_name = review_group_name.lower()

        anyrb = AnyRB()

        description = self._get_description(request, task, svn_path, rev_a, rev_b)
        if review_id is None:
            review_id = anyrb.submit_review(user, rev_a, rev_b, summary=summary, description=description, review_group_name=", ".join((review_group_name, settings.RB_API_DEFAULT_REVIEW_GROUP)),  path=svn_path)
        else:
            anyrb.update_review(user, rev_a, rev_b, review_id, description=description, path=svn_path)

        issue.rb_review_id = review_id
        issue.save()

        context = {
            'review_url' : anyrb.get_review_url(request, review_id),
            'task' : task,
        }

        return render_to_response('submit_review_done.html', context, context_instance=RequestContext(request))

    def _get_submit_form(self, request, task, svn_path):
        user = request.user

        prev_revision = 1
        try:

            head_revision = svn_log_head_revision(user, svn_path)
        except pysvn.ClientError:
            return render_to_response('submit_review_no_such_path.html', {}, context_instance=RequestContext(request))

        try:
            issue = Issue.objects.filter(task=task, student=user).order_by('-update_time')[0]
            prev_revision = issue.svn_commit_id
        except Issue.DoesNotExist:
            pass
        except IndexError:
            pass


        context = {
            "prev_revision" : prev_revision,
            "head_revision" : head_revision,
            "ready_to_submit" : 1,
            "logs" : svn_log_rev_message(user, svn_path),
            "task" : task,
        }

        return render_to_response('submit_review_form.html', context, context_instance=RequestContext(request))


    @method_decorator(login_required)
    def dispatch(self, request, task_id, svn_path="", *args, **kwargs):
        task = get_object_or_404(Task, id=task_id)

        if request.method == "POST":
            return self._submit_review(request, task, svn_path)

        return self._get_submit_form(request, task, svn_path)


def send_error_to_review_form(task_id, errors):
    for key in errors.keys():
        errors[key] = errors[key].encode('utf-8')
    error = urllib.urlencode(errors)
    return HttpResponseRedirect("%s?" % reverse('submit_review', kwargs={'task_id':task_id}) + error)


def save_gr_review_form(request, task_taken):
    if  request.method == "POST":
            id_issue = request.POST.get('id_issue')

            try:
                code = urllib2.urlopen("https://codereview.appspot.com/" + id_issue.strip()).code
            except urllib2.HTTPError, err:
                if err.code == 404:
                    message = u"По адресу " + u"https://codereview.appspot.com/" + id_issue.strip() + u" ничего не найдено."
                    return {'gr_error': message}
                else:
                    pass
            except UnicodeEncodeError, err:
                message = u"Адрес " + u"https://codereview.appspot.com/" + id_issue.strip() + u" не верен."
                return {'gr_error': message}

            try:
                if not id_issue:
                    id_issue = None
                else:
                    id_issue = int(id_issue)
                if task_taken.id_issue_gr_review != id_issue:
                    task_taken.id_issue_gr_review = id_issue
                    task_taken.gr_review_update_time = datetime.datetime.now()
                    task_taken.save()
            except ValueError:
                message = u"Вы ввели не число."
                return {'gr_error': message}
    return {}


def save_pdf_review_form(request, task_taken):
    if request.method == "POST":
        course = task_taken.task.course
        pdf_form = PdfForm(request.POST, request.FILES, extensions=["." + x.name for x in course.filename_extensions.all()])
        if pdf_form.is_valid():
            if 'pdf' in pdf_form.files:
                task_taken.pdf = pdf_form.files['pdf']
                task_taken.pdf_update_time = datetime.datetime.now()
                task_taken.save()
        else:
            message = unicode(strip_tags(pdf_form._errors['pdf']))
            return {'pdf_error': message}
    return {}

def send_task_to_teacher(user, task_taken):
    new_status = TaskTaken.QUEUE
    if task_taken.user_can_change_status(user, new_status):
        task_taken.status_check = new_status
        task_taken.save()


def submit_pdf_gr_form(request, task_id):
    task_id = int(task_id)
    task = get_object_or_404(Task, id=task_id)

    if len(TaskTaken.objects.filter(task__id=task_id, user=request.user)) == 0:
        TaskTaken.objects.create(task=task, user=request.user)

    task_taken = get_object_or_404(TaskTaken, task__id=task_id, user=request.user)
    course = task.course
    if request.method == "POST":
        pdf_error = save_pdf_review_form(request, task_taken)
        gr_error = save_gr_review_form(request, task_taken)
        if pdf_error or gr_error:
            errors = pdf_error
            errors.update(gr_error)
            return send_error_to_review_form(task_id, errors)
        else:
            send_task_to_teacher(request.user, task_taken)
    return HttpResponseRedirect(reverse('submit_review', kwargs={'task_id':task_id}))


def set_colors_to_teachers(request, course):
    user_color = "green"
    colors = ["red", "yellow", "purple", "lightgreen", "DeepSkyBlue", "Peru"]
    color_set = {}
    color_set[request.user.id] = (user_color, request.user.get_full_name())
    teachers = course.teachers.all()
    for i in range(len(teachers)):
        teacher = teachers[i]
        if teacher.id not in color_set:
            if i < len(color_set):
                color_set[teacher.id] = (colors[i], teacher.get_full_name())
            else:
                color_set[teacher.id] = (colors[-1], teacher.get_full_name())
    return color_set


def ajax_get_transcript(request, course_id):
    if not request.is_ajax():
        return HttpResponseForbidden()

    transcript = ""
    try:
        course = Course.objects.get(id=course_id)
        if course.type == Course.TYPE_MANY_TASK_MANY_GROUP:
            color_set = set_colors_to_teachers(request, course)
            context = tasks_list_many_task_many_group(request, course, get_context=True)
            context['color_set'] = color_set
            transcript = render_to_response('course_transcript_many_task_many_group.html', context, context_instance=RequestContext(request))
            transcript = str(transcript)[len("Content-Type: text/html; charset=utf-8"):]

    except ObjectDoesNotExist:
        pass

    data = {
        'transcript': transcript,
    }

    return HttpResponse(json.dumps(data), content_type="application/json")


def queue_tasks_to_check(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if course.type == Course.TYPE_MANY_TASK_MANY_GROUP:
        context = tasks_list_many_task_many_group(request, course, get_context=True)

        return render_to_response('course_queue_many_task_many_group.html', context, context_instance=RequestContext(request))

    #tasks_to_check = TaskTaken.objects.filter(course=course, status_check=TaskTaken.QUEUE)
    return render_to_response('course_queue_tasks_to_check.html', {"course":course}, context_instance=RequestContext(request))


