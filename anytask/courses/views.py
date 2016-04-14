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
import logging
import requests

from courses.models import Course, DefaultTeacher
from groups.models import Group
from tasks.models import TaskTaken, Task
from tasks.views import update_status_check
from years.models import Year
from years.common import get_current_year
from course_statistics import CourseStatistics
from score import TaskInfo
from anysvn.common import svn_log_rev_message, svn_log_head_revision, get_svn_external_url, svn_log_min_revision
from anyrb.common import AnyRB
from anycontest.common import get_contest_info
from issues.models import Issue, Event, IssueFilter

from common.ordered_dict import OrderedDict

from courses.forms import PdfForm, QueueForm, default_teacher_forms_factory, DefaultTeacherForm
from django.utils.html import strip_tags
from filemanager import FileManager
from settings import UPLOAD_ROOT
import os.path

import json

logger = logging.getLogger('django.request')

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
    course_id_as_str = str(course_id)

    if not course.user_can_see_queue(request.user):
        return HttpResponseForbidden()

    issues = Issue.objects.filter(task__course=course)

    f = IssueFilter(request.GET, issues)
    f.set_course(course)

    if f.form.data:
        request.session[course_id_as_str] = f.form.data
    elif course_id_as_str in request.session:
        f.form.data = request.session.get(course_id_as_str)

    context = {
        'course' : course,
        'user_is_teacher' : course.user_is_teacher(request.user),
        'filter': f,
    }
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

    events_with_mark = Event.objects.filter(field_id=8).filter(author__in=course.teachers.all()).order_by('issue','timestamp')
    marks_for_issues = {}
    for event in events_with_mark:
        if event.issue.task.course == course:
            try:
                marks_for_issues[event.issue.id] = float(event.value)
            except Exception as e:
                marks_for_issues[event.issue.id] = 0
                logger.exception("Not a float mark. Exception: '%s'. Issue: '%s'. Event: '%s'.", e, event.issue.id, event.id)

    for group in course.groups.all().order_by('name'):
        student_x_task_x_task_takens = {}

        group_x_task_list[group] = Task.objects.filter(Q(course=course) & (Q(group=group) | Q(group=None))).order_by('weight').select_related()
        group_x_max_score.setdefault(group, 0)

        for task in group_x_task_list[group]:

            if not task.is_hidden:
                group_x_max_score[group] += task.score_max
            if task.task_text is None:
                task.task_text = ''

        issues_students_in_group = Issue.objects.filter(task__in=group_x_task_list[group]).filter(student__group__in=[group]).order_by('student').select_related()

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
                if not task_taken.task.is_hidden and task_taken.id in marks_for_issues:
                    student_summ_scores += marks_for_issues[task_taken.id]

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

    context = {
        'course'        : course,
        'group_information'   : group_x_student_information,
        'group_tasks'   : group_x_task_list,
        'group_x_max_score' : group_x_max_score,

        'user' : user,
        'user_is_attended' : user_is_attended,
        'user_is_attended_special_course' : user_is_attended_special_course,
        'user_is_teacher': course.user_is_teacher(user),
        
        'visible_queue' : course.user_can_see_queue(user),
    }

    return context


def get_tasklist_context(request, course):
    return tasklist_shad_cpp(request, course)

def edit_task(request):
    user = request.user

    if not request.method == 'POST':
        return HttpResponseForbidden()

    hidden_task = False
    if 'hidden_task' in request.POST:
        hidden_task = True

    try:
        task_id = int(request.POST['task_id'])
        task_title = request.POST['task_title'].strip()
        task_text = request.POST['task_text'].strip()
        max_score = int(request.POST['max_score'])
        task = get_object_or_404(Task, id = task_id)
        if task.course.contest_integrated:
            contest_id = int(request.POST['contest_id'])
            problem_id = request.POST['problem_id'].strip()

        task_group_id = request.POST['task_group_id']
        group_id = request.POST['group_id']
        if task_group_id == "":
            group_id = None
        else:
            group_id = int(task_group_id)

    except ValueError: #not int
        return HttpResponseForbidden()

    group = None
    if group_id is not None:
        group = get_object_or_404(Group, id = group_id)

    if not task.course.user_is_teacher(user):
        return HttpResponseForbidden()

    task.is_hidden = hidden_task
    if task.parent_task:
        if task.parent_task.is_hidden:
            task.is_hidden = True

    task.title = task_title
    task.group = group
    task.task_text = task_text
    task.score_max = max_score
    if task.course.contest_integrated:
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

    hidden_task = False
    if 'hidden_task' in request.POST:
        hidden_task = True

    tasks = []

    try:
        course_id = int(request.POST['course_id'])
        max_score = int(request.POST['max_score'])
        course = get_object_or_404(Course, id = course_id)

        if course.contest_integrated:
            contest_id = int(request.POST['contest_id'])

        task_group_id = request.POST['task_group_id']

        if task_group_id == "":
            group_id = None
        else:
            group_id = int(task_group_id)

        parent_id = request.POST['parent_id']
        if not parent_id or parent_id == 'null':
            parent_id = None
        else:
            parent_id = int(parent_id)

    except ValueError:  # not int
        return HttpResponseForbidden()

    if 'contest_problems[]' not in request.POST:
        try:
            tasks.append({})
            tasks[0]['task_title'] = request.POST['task_title'].strip()
            tasks[0]['task_text'] = request.POST['task_text'].strip()
            if course.contest_integrated:
                tasks[0]['problem_id'] = request.POST['problem_id'].strip()

        except ValueError: #not int
            return HttpResponseForbidden()
    else:
        got_info, contest_info = get_contest_info(contest_id)
        if got_info:
            contest_problems = dict(request.POST)['contest_problems[]']
            for problem in contest_info['problems']:
                if problem['problemId'] in contest_problems:
                    tasks.append({})
                    tasks[-1]['task_title'] = problem['problemTitle']
                    tasks[-1]['task_text'] = problem['statement']
                    tasks[-1]['problem_id'] = problem['alias']
        elif "You're not allowed to view this contest." in contest_info:
            return HttpResponse(json.dumps({'is_error': True, 'error': u"У anytask нет прав на данный контест."}),
                                content_type="application/json")
        else:
            return HttpResponseForbidden()



    group = None
    if group_id is not None:
        group = get_object_or_404(Group, id = group_id)
    parent = None
    if parent_id is not None:
        parent = get_object_or_404(Task, id = parent_id)

    if not course.user_can_edit_course(user):
        return HttpResponseForbidden()

    for task in tasks:
        max_weight_query = Task.objects.filter(course=course)
        if group:
            max_weight_query = max_weight_query.filter(group=group)
        if parent:
            max_weight_query = max_weight_query.filter(parent_task=parent)

        _, max_weight = max_weight_query.aggregate(Max('weight')).items()[0]
        if max_weight is None:
            max_weight = 0
        max_weight += 1

        real_task = Task()
        real_task.course = course
        real_task.group = group
        real_task.parent_task = parent
        real_task.weight = max_weight
        real_task.title = task['task_title']
        real_task.task_text = task['task_text']
        real_task.score_max = max_score
        if course.contest_integrated:
            real_task.contest_id = contest_id
            real_task.problem_id = task['problem_id']
        real_task.is_hidden = hidden_task
        real_task.updated_by = user
        real_task.save()

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


def default_teachers_generate_form(course, post_data=None):
    groups_teacher = {}
    groups_forms = {}
    groups = course.groups.all().order_by('name')

    for default_teacher in DefaultTeacher.objects.filter(course=course).filter(group__in=groups):
        groups_teacher[default_teacher.group.id] = default_teacher.teacher

    for group in groups:
        teacher = groups_teacher.get(group.id)
        groups_forms[group] = default_teacher_forms_factory(course, group, teacher, post_data)
    return groups_forms

def course_settings(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    context = {'course' : course,
               'visible_queue' : course.user_can_see_queue(request.user),
               'user_is_teacher' : course.user_is_teacher(request.user),
    }

    if request.method != "POST":
        form = DefaultTeacherForm(course)
        context['form'] = form
        return render_to_response('courses/settings.html', context, context_instance=RequestContext(request))

    form = DefaultTeacherForm(course, request.POST)
    context['form'] = form

    if not form.is_valid():
        return render_to_response('courses/settings.html', context, context_instance=RequestContext(request))

    for group_key, teacher_id in form.cleaned_data.iteritems():
        teacher_id = int(teacher_id)
        group = form.groups[group_key]
        if teacher_id == 0:
            DefaultTeacher.objects.filter(course=course).filter(group=group).delete()
        else:
            teacher = User.objects.get(pk=teacher_id)
            default_teacher, _ = DefaultTeacher.objects.get_or_create(course=course, group=group)
            default_teacher.teacher = teacher
            default_teacher.save()

    return HttpResponseRedirect('')

@login_required
def get_contest_problems(request):
    course = get_object_or_404(Course, id=request.POST['course_id'])

    if not course.user_can_edit_course(request.user):
        return HttpResponseForbidden()

    if request.method != 'POST':
        return HttpResponseForbidden()

    contest_id = request.POST['contest_id']
    is_error = False
    error = ''
    problems = []

    problem_req = requests.get(settings.CONTEST_API_URL + 'problems?contestId=' + str(contest_id),
                               headers={'Authorization': 'OAuth ' + settings.CONTEST_OAUTH})
    problem_req = problem_req.json()

    if 'error' in problem_req:
        is_error = True
        if 'IndexOutOfBoundsException' in problem_req['error']['name']:
            error = u'Такого контеста не существует'
        else:
            error = u'Ошибка Я.Контеста: ' + problem_req['error']['message']
    else:
        problems = problem_req['result']['problems']

    return HttpResponse(json.dumps({'problems':problems, 'is_error':is_error, 'error':error}), content_type="application/json")
