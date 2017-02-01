#coding: utf-8
import pprint

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext
from django.core.exceptions import PermissionDenied
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

from courses.models import Course, DefaultTeacher, StudentCourseMark, MarkField, FilenameExtension
from groups.models import Group
from tasks.models import TaskTaken, Task, TaskGroupRelations
from tasks.views import update_status_check, prettify_contest_task_text
from years.models import Year
from years.common import get_current_year
from course_statistics import CourseStatistics
from score import TaskInfo
from anysvn.common import svn_log_rev_message, svn_log_head_revision, get_svn_external_url, svn_log_min_revision
from anyrb.common import AnyRB
from anycontest.common import get_contest_info, FakeResponse
from issues.models import Issue, Event, IssueFilter
from issues.model_issue_status import IssueStatus
from users.forms import InviteActivationForm
from users.models import UserProfile

from common.ordered_dict import OrderedDict

from courses.forms import PdfForm, QueueForm, default_teacher_forms_factory, DefaultTeacherForm
from django.utils.html import strip_tags
from filemanager import FileManager
from settings import UPLOAD_ROOT
import os.path

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML

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

    active_profiles = UserProfile.objects.filter(Q(user_status__tag='active')|Q(user_status__tag=None))
    active_students = []
    for profile in active_profiles:
        active_students.append(profile.user)

    issues = Issue.objects.filter(task__course=course, student__in=active_students).order_by('update_time')

    f = IssueFilter(request.GET, issues)
    f.set_course(course)

    if f.form.data:
        request.session[course_id_as_str] = f.form.data
    elif course_id_as_str in request.session:
        f.form.data = request.session.get(course_id_as_str)

    f.form.helper = FormHelper(f.form)
    f.form.helper.form_method = 'get'
    # f.form.helper.label_class = 'col-md-4'
    # f.form.helper.field_class = 'selectpicker'
    f.form.helper.layout.append(HTML(u"""<div class="form-group row">
                                           <button id="button_filter" class="btn btn-secondary pull-xs-right" type="submit">Применить</button>
                                         </div>"""))

    schools = course.school_set.all()

    context = {
        'course': course,
        'user_is_teacher': course.user_is_teacher(request.user),
        'filter': f,
        'school': schools[0] if schools else '',
    }
    return render_to_response('courses/queue.html', context, context_instance=RequestContext(request))

@login_required
def gradebook(request, course_id, task_id=None, group_id=None):
    """Page with course related information
    contexts:
        - tasklist
        - tasks_description
    """
    user = request.user
    if not user.get_profile().is_active():
        raise PermissionDenied

    course = get_object_or_404(Course, id=course_id)
    if task_id:
        task = get_object_or_404(Task, id=task_id)
    else:
        task = None

    if group_id:
        group = get_object_or_404(Group, id=group_id)
    else:
        group = None

    schools = course.school_set.all()

    if course.private and not course.user_is_attended(request.user):
        return render_to_response('courses/course_forbidden.html',
                                  {"course": course,
                                   'school': schools[0] if schools else '',
                                   'invite_form': InviteActivationForm()},
                                  context_instance=RequestContext(request))

    tasklist_context = tasklist_shad_cpp(request, course, task, group)

    context = tasklist_context
    context['tasklist_template'] = 'courses/tasklist/shad_cpp.html'
    context['task_types'] = dict(Task().TASK_TYPE_CHOICES).items()
    context['group_gradebook'] = True if group else False
    context['show_hidden_tasks'] = request.session.get(str(request.user.id) + '_' + str(course.id) + '_show_hidden_tasks', False)
    context['school'] = schools[0] if schools else ''

    return render_to_response('courses/gradebook.html', context, context_instance=RequestContext(request))


@login_required
def course_page(request, course_id):
    """Page with course related information
    contexts:
        - tasklist
        - tasks_description
    """
    user = request.user
    if not user.get_profile().is_active():
        raise PermissionDenied

    course = get_object_or_404(Course, id=course_id)
    schools = course.school_set.all()

    if course.private and not course.user_is_attended(request.user):
        return render_to_response('courses/course_forbidden.html',
                                  {"course": course,
                                   'school': schools[0] if schools else '',
                                   'invite_form': InviteActivationForm()},
                                  context_instance=RequestContext(request))
    course.can_edit = course.user_can_edit_course(user)
    if course.can_edit:
        groups = course.groups.all().order_by('name')
        tasks = [{'group':tgr.group, 'task': tgr.task} for tgr in TaskGroupRelations.objects.filter(task__course=course, group__in=groups, deleted=False).order_by('group','position')]
    else:
        groups = Group.objects.filter(students=user, course__in=[course])
        tasks = set([tgr.task for tgr in TaskGroupRelations.objects.filter(task__course=course, group__in=groups, deleted=False).order_by('group', 'position')])

    if StudentCourseMark.objects.filter(student=user, course=course):
        mark = StudentCourseMark.objects.get(student=user, course=course).mark
    else:
        mark = None

    context = {}

    context['course'] = course
    context['tasks'] = tasks
    context['mark'] = mark if mark else '--'
    context['visible_queue'] = course.user_can_see_queue(user),
    context['user_is_teacher'] = course.user_is_teacher(user)
    context['task_types'] = dict(Task().TASK_TYPE_CHOICES).items()
    context['show_hidden_tasks'] = request.session.get(str(request.user.id) + '_' + str(course.id) + '_show_hidden_tasks', False)
    context['school'] = schools[0] if schools else ''

    return render_to_response('courses/course.html', context, context_instance=RequestContext(request))


@login_required
def seminar_page(request, course_id, task_id):
    """Page with course related information
    contexts:
        - tasklist
        - tasks_description
    """

    user = request.user
    if not user.get_profile().is_active():
        raise PermissionDenied

    course = get_object_or_404(Course, id=course_id)
    task = get_object_or_404(Task, id=task_id)
    schools = course.school_set.all()

    if course.private and not course.user_is_attended(request.user):
        return render_to_response('courses/course_forbidden.html',
                                  {"course": course,
                                   'school': schools[0] if schools else '',
                                   'invite_form': InviteActivationForm()},
                                  context_instance=RequestContext(request))
    course.can_edit = course.user_can_edit_course(user)

    if course.can_edit:
        groups = task.groups.all().order_by('name')
        tasks = [{'group': tgr.group, 'task': tgr.task} for tgr in
                 TaskGroupRelations.objects.filter(task__parent_task=task, group__in=groups, deleted=False).order_by('group',
                                                                                                                  'position')]
    else:
        groups = Group.objects.filter(students=user, course__in=[course])
        tasks = set([tgr.task for tgr in
                     TaskGroupRelations.objects.filter(task__parent_task=task, group__in=groups, deleted=False).order_by(
                         'group', 'position')])
    if Issue.objects.filter(task=task, student=user):
        mark = Issue.objects.get(task=task, student=user).mark
    else:
        mark = None

    context = {}
    context['course'] = course
    context['tasks'] = tasks
    context['mark'] = mark if mark else '--'
    context['visible_queue'] = course.user_can_see_queue(user),
    context['user_is_teacher'] = course.user_is_teacher(user)
    context['seminar'] = task
    context['task_types'] = dict(Task().TASK_TYPE_CHOICES).items()
    context['show_hidden_tasks'] = request.session.get(str(request.user.id) + '_' + str(course.id) + '_show_hidden_tasks', False)
    context['school'] = schools[0] if schools else ''

    return render_to_response('courses/course.html', context, context_instance=RequestContext(request))


def tasklist_shad_cpp(request, course, seminar=None, group=None):

    user = request.user
    user_is_attended = False
    user_is_attended_special_course = False
    is_seminar = False

    if seminar:
        is_seminar = True
        groups = seminar.groups.all().order_by('name')
    else:
        groups = course.groups.all().order_by('name')

    course.can_edit = course.user_can_edit_course(user)
    if course.can_be_chosen_by_extern:
        course.groups.add(course.group_with_extern)

    if group:
        groups = [group]

    group_x_student_x_task_takens = OrderedDict()
    group_x_task_list = {}
    group_x_max_score = {}
    default_teacher = {}
    show_hidden_tasks = request.session.get(str(request.user.id) + '_' + str(course.id) + '_show_hidden_tasks', False)

    for group in groups:
        student_x_task_x_task_takens = {}

        if is_seminar:
            tasks_for_groups = TaskGroupRelations.objects.filter(task__course=course, group=group, deleted=False, task__parent_task=seminar).order_by('position').select_related('task')
        else:
            tasks_for_groups = TaskGroupRelations.objects.filter(task__course=course, group=group, deleted=False, task__parent_task=None).order_by('position').select_related('task')

        if show_hidden_tasks:
            group_x_task_list[group] = [x.task for x in tasks_for_groups]
        else:
            group_x_task_list[group] = [x.task for x in tasks_for_groups if not x.task.is_hidden]

        group_x_max_score.setdefault(group, 0)

        for task in group_x_task_list[group]:

            if not task.is_hidden:
                if task.type == task.TYPE_SEMINAR:
                    group_x_max_score[group] += sum([x.score_max for x in task.children.all()])
                else:
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

            student_task_takens = issues_x_student[student.id]

            task_x_task_taken = {}
            student_summ_scores = 0
            for task_taken in student_task_takens:
                task_x_task_taken[task_taken.task.id] = task_taken
                if not task_taken.task.is_hidden:
                    student_summ_scores += task_taken.mark

            student_x_task_x_task_takens[student] = (task_x_task_taken, student_summ_scores)

        group_x_student_x_task_takens[group] = student_x_task_x_task_takens

        try:
            default_teacher[group] = DefaultTeacher.objects.get(course=course, group=group).teacher
        except DefaultTeacher.DoesNotExist:
            default_teacher[group] = None


    group_x_student_information = OrderedDict()
    for group,student_x_task_x_task_takens in group_x_student_x_task_takens.iteritems():
        group_x_student_information.setdefault(group, [])

        for student in sorted(student_x_task_x_task_takens.keys(), key=lambda x: u"{0} {1}".format(x.last_name, x.first_name)):
            if user == student:
                user_is_attended = True
            elif not course.user_can_see_transcript(user, student):
                continue

            mark_id, course_mark = get_course_mark(course, group, student)

            group_x_student_information[group].append((student,
                                                       student_x_task_x_task_takens[student][0],
                                                       student_x_task_x_task_takens[student][1],
                                                       mark_id,
                                                       course_mark))

    context = {
        'course': course,
        'course_mark_system_vals': course.mark_system.marks.all() if course.mark_system else None,
        'group_information': group_x_student_information,
        'group_tasks': group_x_task_list,
        'group_x_max_score': group_x_max_score,
        'default_teacher': default_teacher,

        'user': user,
        'user_is_attended': user_is_attended,
        'user_is_attended_special_course': user_is_attended_special_course,
        'user_is_teacher': course.user_is_teacher(user),

        'seminar': seminar,
        'visible_queue': course.user_can_see_queue(user),
        'visible_hide_button': Task.objects.filter(Q(course=course) & Q(is_hidden=True)).count(),
        'show_hidden_tasks' : show_hidden_tasks
    }

    return context


def get_tasklist_context(request, course):
    return tasklist_shad_cpp(request, course)


def get_course_mark(course, group, student):
    mark_id = -1
    course_mark = '--'

    try:
        student_course_mark = StudentCourseMark.objects.get(course=course, group=group, student=student)
        if student_course_mark.mark:
            mark_id = student_course_mark.mark.id
            course_mark = unicode(student_course_mark)
    except StudentCourseMark.DoesNotExist:
        pass

    return mark_id, course_mark


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

    if course_information and not course_information.startswith(u'<div class="not-sanitize">'):
        course_information = u'<div class="not-sanitize">' + course_information + u'</div>'
    course.information = course_information
    course.save()

    return HttpResponse(json.dumps({'info': course_information}),
                        content_type="application/json")

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


def get_filename_extensions(course):
    extensions = FilenameExtension.objects.all().order_by('name')
    course_extensions = course.filename_extensions.all()
    return [(ext, True) if ext in course_extensions else (ext, False) for ext in extensions]


@login_required
def course_settings(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    schools = course.school_set.all()

    tasks_with_contest = {}
    if course.is_contest_integrated():
        for task in course.task_set.filter(contest_integrated=True, is_hidden=False):
            tasks_with_contest[task.contest_id] = tasks_with_contest.get(task.contest_id, list()) + [task]

    context = {'course': course,
               'visible_queue': course.user_can_see_queue(request.user),
               'user_is_teacher': course.user_is_teacher(request.user),
               'school': schools[0] if schools else '',
               'tasks_with_contest': tasks_with_contest,
               }

    if request.method != "POST":
        form = DefaultTeacherForm(course)
        context['form'] = form
        context['file_extensions'] = get_filename_extensions(course)
        return render_to_response('courses/settings.html', context, context_instance=RequestContext(request))

    form = DefaultTeacherForm(course, request.POST)
    context['form'] = form

    if not form.is_valid():
        context['file_extensions'] = get_filename_extensions(course)
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

    if 'rb_extensions[]' in request.POST:
        course.filename_extensions = request.POST.getlist('rb_extensions[]')
    else:
        course.filename_extensions.clear()

    if 'show_task_one_file_upload' in request.POST:
        course.show_task_one_file_upload = True
    else:
        course.show_task_one_file_upload = False

    if 'default_task_one_file_upload' in request.POST:
        course.default_task_one_file_upload = True
    else:
        course.default_task_one_file_upload = False

    if 'show_accepted_after_contest_ok' in request.POST:
        course.show_accepted_after_contest_ok = True
    else:
        course.show_accepted_after_contest_ok= False

    if 'default_task_one_file_upload' in request.POST:
        course.default_accepted_after_contest_ok = True
    else:
        course.default_accepted_after_contest_ok = False

    course.save()

    return HttpResponseRedirect('')


def change_visibility_hidden_tasks(request):
    if not request.method == 'POST':
        return HttpResponseForbidden()

    course = get_object_or_404(Course, id=int(request.POST['course_id']))
    if not course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    session_var_name = str(request.user.id) + '_' + request.POST['course_id'] + '_show_hidden_tasks'
    request.session[session_var_name] = not request.session.get(session_var_name, False)

    return HttpResponse("OK")


@login_required
def set_course_mark(request):
    if request.method != 'POST':
        return HttpResponseForbidden()

    course = get_object_or_404(Course, id=request.POST['course_id'])
    group = get_object_or_404(Group, id=request.POST['group_id'])
    student = get_object_or_404(User, id=request.POST['student_id'])
    if request.POST['mark_id'] != '-1':
        mark = get_object_or_404(MarkField, id=request.POST['mark_id'])
    else:
        mark = MarkField()

    student_course_mark = StudentCourseMark()
    try:
        student_course_mark = StudentCourseMark.objects.get(course=course, group=group, student=student)
    except StudentCourseMark.DoesNotExist:
        student_course_mark.course = course
        student_course_mark.group = group
        student_course_mark.student = student

    student_course_mark.teacher = request.user
    student_course_mark.update_time = datetime.datetime.now()
    student_course_mark.mark = mark
    student_course_mark.save()

    return HttpResponse(json.dumps({'mark': unicode(mark), 'student_course_mark_id': student_course_mark.id}),
                        content_type="application/json")


@login_required
def set_task_mark(request):
    if request.method != 'POST':
        return HttpResponseForbidden()

    task_id = request.POST['task_id']
    task = get_object_or_404(Task, id=task_id)
    if not task.course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    issue, created = Issue.objects.get_or_create(task_id=task_id, student_id=request.POST['student_id'])

    mark = 0
    if request.POST['mark_value'] == '-':
        issue.set_status_by_tag(IssueStatus.STATUS_NEW)
    else:
        mark = float(request.POST['mark_value'])
        if mark <= 0:
            issue.set_status_by_tag(IssueStatus.STATUS_REWORK)
        else:
            issue.set_status_by_tag(IssueStatus.STATUS_ACCEPTED)

    issue.set_byname('mark', mark)

    return HttpResponse(json.dumps({'mark': mark,
                                    'color': issue.status_field.color}),
                        content_type="application/json")


@login_required
def change_table_tasks_pos(request):
    if request.method != 'POST':
        return HttpResponseForbidden()

    course = get_object_or_404(Course, id=int(request.POST['course_id']))
    if not course.user_is_teacher(request.user):
        return HttpResponseForbidden()

    group = get_object_or_404(Group, id=int(request.POST['group_id']))
    deleting_ids_from_groups = json.loads(request.POST['deleting_ids_from_groups'])
    if deleting_ids_from_groups:
        for task_id, group_ids in deleting_ids_from_groups.iteritems():

            group_ids = list(set(group_ids))
            task = get_object_or_404(Task, id=int(task_id))
            task_groups = task.groups.filter(id__in=group_ids)
            for tg in task_groups:
                if Issue.objects.filter(task=task, student__in=tg.students.all()).count():
                    return HttpResponseForbidden()
            task.groups.remove(*task.groups.filter(id__in=group_ids))
            task.save()

            for task_relations in TaskGroupRelations.objects.filter(task=task, group__id__in=group_ids):
                task_relations.deleted = True
                task_relations.save()


    if 'task_deleted[]' in request.POST:
        task_deleted = map(lambda x: int(x), dict(request.POST)['task_deleted[]'])
        for task in Task.objects.filter(id__in=task_deleted):
            if not Issue.objects.filter(task=task).count():
                try:
                    task.delete()
                    TaskGroupRelations.objects.get(task=task, group=group).delete()
                except TaskGroupRelations.DoesNotExist:
                    pass
            else:
                return HttpResponseForbidden()

    if 'task_order[]' in request.POST:
        task_order = map(lambda x: int(x), dict(request.POST)['task_order[]'])

        for task_relations in TaskGroupRelations.objects.select_related('task') \
                .filter(task__id__in=task_order).filter(group=group):
            task_relations.position = task_order.index(task_relations.task.id)
            task_relations.save()

    return HttpResponse("OK")


@login_required
def ajax_update_contest_tasks(request):
    if not request.is_ajax():
        return HttpResponseForbidden()

    if 'tasks_with_contest[]' not in request.POST or 'contest_id' not in request.POST:
        return HttpResponseForbidden()

    contest_id = int(request.POST['contest_id'])

    response = {'is_error': False,
                'contest_id': contest_id,
                'error': '',
                'tasks_title': {}}

    got_info, contest_info = get_contest_info(contest_id)
    if got_info:
        problem_req = FakeResponse()
        problem_req = requests.get(settings.CONTEST_API_URL + 'problems?contestId=' + str(contest_id),
                                   headers={'Authorization': 'OAuth ' + settings.CONTEST_OAUTH})
        problems = []
        if 'error' in problem_req:
            response['is_error'] = True
            if 'IndexOutOfBoundsException' in problem_req['error']['name']:
                response['error'] = u'Такого контеста не существует'
            else:
                response['error'] = u'Ошибка Я.Контеста: ' + problem_req['error']['message']
        if 'result' in problem_req.json():
            problems = problem_req.json()['result']['problems']

        contest_responses = [contest_info, problems]
    else:
        response['is_error'] = True
        if "You're not allowed to view this contest." in contest_info:
            response['error'] = u"У anytask нет прав на данный контест"
        elif "Contest with specified id does not exist." in contest_info:
            response['error'] = u'Такого контеста не существует'
        else:
            response['error'] = u'Ошибка Я.Контеста: ' + contest_info

    if not response['is_error']:
        for task in Task.objects.filter(id__in=dict(request.POST)['tasks_with_contest[]']):
            alias = task.problem_id
            if contest_id != task.contest_id:
                continue

            for problem in contest_responses[0]['problems']:
                if problem['alias'] == alias:
                    task.title = problem['problemTitle']
                    task.task_text = prettify_contest_task_text(problem['statement'])
                    if 'endTime' in contest_responses[0]:
                        deadline = contest_responses[0]['endTime'].split('+')[0]
                        task.deadline_time = datetime.datetime.strptime(deadline, '%Y-%m-%dT%H:%M:%S.%f')
                    else:
                        task.deadline_time = None
                    break

            for problem in contest_responses[1]:
                if problem['title'] == alias:
                    if 'score' in problem:
                        task.score_max = problem['score']

            task.save()
            response['tasks_title'][task.id] = task.title

    return HttpResponse(json.dumps(response),
                        content_type="application/json")
