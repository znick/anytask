# coding: utf-8

from django.shortcuts import render, get_object_or_404
from django.http import Http404, QueryDict
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.utils.timezone import localtime, now
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.http import require_http_methods

from collections import defaultdict, Counter
import datetime
import logging
import requests
from reversion import revisions as reversion

from courses.models import Course, DefaultTeacher, StudentCourseMark, MarkField, FilenameExtension
from groups.models import Group
from tasks.models import Task, TaskGroupRelations
from years.models import Year
from years.common import get_current_year
from anycontest.common import get_contest_info, FakeResponse
from issues.models import Issue
from issues.issueFilter import IssueFilter
from issues.model_issue_status import IssueStatus
from issues.views import contest_rejudge
from users.forms import InviteActivationForm
from users.models import UserProfile
from courses import pythontask
from lessons.models import Lesson

from common.ordered_dict import OrderedDict
from common.timezone import convert_datetime

from courses.forms import default_teacher_forms_factory, DefaultTeacherForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML

import json

logger = logging.getLogger('django.request')

QUEUE_SESSION_PREFIX = 'queue'
QUEUE_COLUMN_ORDER = {
    "1": ["student__last_name", "student__first_name"],
    "2": ["task__title"],
    "3": ["update_time"],
    "4": ["mark"],
    "5": ["responsible__last_name", "responsible__first_name"],
}


@require_http_methods(['GET'])
@login_required
def queue_page(request, course_id):
    user = request.user
    course = get_object_or_404(Course, id=course_id)

    if not course.user_can_see_queue(user):
        raise PermissionDenied

    f = IssueFilter(request.GET, {})
    f.set_course(course, user)
    session_key = '_'.join([QUEUE_SESSION_PREFIX, str(course_id)])
    if request.GET:
        request.session[session_key] = f.form.data
    elif session_key in request.session:
        f.form.data = request.session.get(session_key)
    f.form.helper = FormHelper(f.form)
    f.form.helper.form_method = 'get'
    f.form.helper.layout.append(
        HTML(
            u"""
            <div class="form-group row">
            <button id="button_clear" class="btn btn-secondary" type="button">{0}</button>
            </div>
            <div class="form-group row">
            <button id="button_filter" class="btn btn-primary" type="button">{1}</button>
            </div>
            """.format(_(u'ochistit'), _(u'primenit'))
        )
    )

    schools = course.school_set.all()

    context = {
        'course': course,
        'user_is_teacher': course.user_is_teacher(user),
        'visible_attendance_log': course.user_can_see_attendance_log(user),
        'filter': f,
        'school': schools[0] if schools else '',
        'full_width_page': True,
        'timezone': user.profile.time_zone
    }
    return render(request, 'courses/queue.html', context)


def set_order_direction(values, direction):
    if direction == "desc":
        return map(lambda x: "-" + x, values)
    return values


@require_http_methods(['POST'])
@login_required
def ajax_get_queue(request):
    user = request.user

    if "draw" not in request.POST or "course_id" not in request.POST:
        raise PermissionDenied

    course = get_object_or_404(Course, id=request.POST['course_id'])

    if not course.user_can_see_queue(user):
        raise PermissionDenied

    issues = Issue.objects.filter(
        Q(task__course=course)
        & (Q(student__profile__user_status__tag='active') | Q(student__profile__user_status__tag=None))
        & Q(student__group__course=course)
    ).exclude(
        task__type=Task.TYPE_SEMINAR,
    ).exclude(
        task__type=Task.TYPE_MATERIAL,
    ).distinct().select_related('student', 'task', 'responsible', 'status_field')

    order = []
    for order_info in json.loads(request.POST.get("order", "[]")):
        order.extend(set_order_direction(QUEUE_COLUMN_ORDER.get(str(order_info.get("column"))), order_info.get("dir")))
    issues = issues.order_by(*order)

    f = IssueFilter(QueryDict(request.POST["filter"]), issues)
    f.set_course(course, user)
    f.set_data(request.POST)
    session_key = '_'.join([QUEUE_SESSION_PREFIX, str(course.id)])
    if f.form.data:
        request.session[session_key] = f.form.data
    f.qs.count()

    return HttpResponse(json.dumps(f.response), content_type="application/json")


@require_http_methods(['GET'])
@login_required
def gradebook(request, course_id, task_id=None, group_id=None):
    """Page with course related information
    contexts:
        - tasklist
        - tasks_description
    """
    user = request.user

    if not user.profile.is_active():
        raise PermissionDenied

    course = get_object_or_404(Course, id=course_id)
    if task_id:
        task = get_object_or_404(Task, id=task_id, type=Task.TYPE_SEMINAR)
    else:
        task = None

    if group_id:
        group = get_object_or_404(Group, id=group_id)
    else:
        group = None

    schools = course.school_set.all()

    if course.private and not course.user_is_attended(request.user):
        return render(request, 'courses/course_forbidden.html',
                      {"course": course,
                       'school': schools[0] if schools else '',
                       'invite_form': InviteActivationForm()})
    lang = request.session.get('django_language', user.profile.language)
    issue_statuses = []
    seminar_color = IssueStatus.COLOR_DEFAULT
    for status in course.issue_status_system.statuses.all():
        issue_statuses.append((status.color, status.get_name(lang)))
        if status.tag == IssueStatus.STATUS_SEMINAR:
            seminar_color = status.color

    tasklist_context = tasklist_shad_cpp(request, course, task, group)

    context = tasklist_context
    context.update({
        'tasklist_template': 'courses/tasklist/shad_cpp.html',
        'task_types': dict(Task().TASK_TYPE_CHOICES).items(),
        'group_gradebook': True if group else False,
        'show_hidden_tasks': request.session.get(
            str(request.user.id) + '_' + str(course.id) + '_show_hidden_tasks', False
        ),
        'show_academ_users': request.session.get(
            str(request.user.id) + '_' + str(course.id) + '_show_academ_users', True
        ),
        'school': schools[0] if schools else '',
        'full_width_page': True,
        'issue_statuses': issue_statuses,
        'seminar_color': seminar_color,
    })

    return render(request, 'courses/gradebook.html', context)


@require_http_methods(['GET'])
@login_required
def course_page(request, course_id):
    """Page with course related information
    contexts:
        - tasklist
        - tasks_description
    """
    user = request.user
    if not user.profile.is_active():
        raise PermissionDenied

    course = get_object_or_404(Course, id=course_id)
    if course.is_python_task:
        return pythontask.tasks_list(request, course)

    schools = course.school_set.all()

    if course.private and not course.user_is_attended(request.user):
        return render(request, 'courses/course_forbidden.html',
                      {"course": course,
                       'school': schools[0] if schools else '',
                       'invite_form': InviteActivationForm()})
    course.can_edit = course.user_can_edit_course(user)
    if course.can_edit:
        groups = course.groups.all().order_by('name')
        tasks = [{'group': tgr.group, 'task': tgr.task} for tgr in
                 TaskGroupRelations.objects.filter(task__course=course, group__in=groups, deleted=False).order_by(
                     'group', 'position')]
    else:
        groups = Group.objects.filter(students=user, course__in=[course])
        tasks = TaskGroupRelations.objects.filter(
            task__course=course, group__in=groups, deleted=False
        ).order_by(
            'group', 'position'
        ).values_list(
            'task__id', flat=True
        ).distinct()
        tasks = Task.objects.filter(id__in=tasks)

    if StudentCourseMark.objects.filter(student=user, course=course):
        mark = StudentCourseMark.objects.get(student=user, course=course).mark
    else:
        mark = None

    context = {}

    context['course'] = course
    context['tasks'] = tasks
    context['mark'] = mark or '--'
    context['visible_queue'] = course.user_can_see_queue(user),
    context['visible_attendance_log'] = course.user_can_see_attendance_log(user),
    context['user_is_teacher'] = course.user_is_teacher(user)
    context['task_types'] = dict(Task().TASK_TYPE_CHOICES).items()
    context['show_hidden_tasks'] = request.session.get(
        str(request.user.id) + '_' + str(course.id) + '_show_hidden_tasks', False)
    context['school'] = schools[0] if schools else ''
    context['visible_attendance_log'] = course.user_can_see_attendance_log(request.user)
    context['jupyterhub_url'] = getattr(settings, 'JUPYTERHUB_URL', '')

    return render(request, 'courses/course.html', context)


@login_required
def seminar_page(request, course_id, task_id):
    """Page with course related information
    contexts:
        - tasklist
        - tasks_description
    """

    user = request.user
    if not user.profile.is_active():
        raise PermissionDenied

    course = get_object_or_404(Course, id=course_id)
    task = get_object_or_404(Task, id=task_id, type=Task.TYPE_SEMINAR)
    schools = course.school_set.all()

    if course.private and not course.user_is_attended(request.user):
        return render(request, 'courses/course_forbidden.html',
                      {"course": course,
                       'school': schools[0] if schools else '',
                       'invite_form': InviteActivationForm()})
    course.can_edit = course.user_can_edit_course(user)

    if course.can_edit:
        groups = task.groups.all().order_by('name')
        tasks = [{'group': tgr.group, 'task': tgr.task} for tgr in
                 TaskGroupRelations.objects.filter(task__parent_task=task, group__in=groups, deleted=False).order_by(
                     'group',
                     'position')]
    else:
        groups = Group.objects.filter(students=user, course__in=[course])
        tasks = TaskGroupRelations.objects.filter(
            task__course=course, group__in=groups, deleted=False
        ).order_by(
            'group', 'position'
        ).values_list(
            'task__id', flat=True
        ).distinct()
        tasks = Task.objects.filter(id__in=tasks)
    if Issue.objects.filter(task=task, student=user):
        mark = Issue.objects.get(task=task, student=user).mark
    else:
        mark = None

    context = {}
    context['course'] = course
    context['tasks'] = tasks
    context['mark'] = mark if mark else '--'
    context['visible_queue'] = course.user_can_see_queue(user),
    context['visible_attendance_log'] = course.user_can_see_attendance_log(user),
    context['user_is_teacher'] = course.user_is_teacher(user)
    context['seminar'] = task
    context['task_types'] = dict(Task().TASK_TYPE_CHOICES).items()
    context['show_hidden_tasks'] = request.session.get(
        str(request.user.id) + '_' + str(course.id) + '_show_hidden_tasks', False)
    context['school'] = schools[0] if schools else ''
    context['visible_attendance_log'] = course.user_can_see_attendance_log(request.user)

    return render(request, 'courses/course.html', context)


def tasklist_shad_cpp(request, course, seminar=None, group=None):
    user = request.user
    user_is_attended = False
    user_is_attended_special_course = False

    if seminar:
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
    show_academ_users = request.session.get(str(request.user.id) + '_' + str(course.id) + '_show_academ_users', True)

    academ_students = []

    for group in groups:
        student_x_task_x_task_takens = {}

        tasks_for_groups = TaskGroupRelations.objects \
            .filter(task__course=course, group=group, deleted=False, task__parent_task=seminar) \
            .exclude(task__type=Task.TYPE_MATERIAL) \
            .distinct() \
            .order_by('position') \
            .prefetch_related('task__groups') \
            .select_related('task')

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

        issues_students_in_group = Issue.objects \
            .filter(task__in=group_x_task_list[group], student__group__in=[group]) \
            .order_by('student') \
            .select_related("task") \
            .prefetch_related('task__groups', 'task')

        issues_x_student = defaultdict(list)
        for issue in issues_students_in_group.all():
            student_id = issue.student.id
            issues_x_student[student_id].append(issue)

        students = group.students.filter(is_active=True)
        not_active_students = UserProfile.objects.filter(
            Q(user__in=group.students.filter(is_active=True))
            & (Q(user_status__tag='not_active') | Q(user_status__tag='academic'))
        )
        academ_students += [x.user for x in not_active_students]
        if not show_academ_users:
            students = set(students) - set(academ_students)

        for student in students:
            if user == student:
                user_is_attended = True
                user_is_attended_special_course = True

            student_task_takens = issues_x_student[student.id]

            task_x_task_taken = {}
            student_summ_scores = 0
            for task_taken in student_task_takens:
                task_x_task_taken[task_taken.task.id] = task_taken
                if not task_taken.task.is_hidden:
                    if task_taken.task.type == Task.TYPE_SEMINAR or \
                            task_taken.task.score_after_deadline or \
                            not (not task_taken.task.score_after_deadline
                                 and task_taken.is_status_accepted_after_deadline()):
                        student_summ_scores += task_taken.mark

            student_x_task_x_task_takens[student] = (task_x_task_taken, student_summ_scores)

        group_x_student_x_task_takens[group] = student_x_task_x_task_takens

        try:
            default_teacher[group] = DefaultTeacher.objects.get(course=course, group=group).teacher
        except DefaultTeacher.DoesNotExist:
            default_teacher[group] = None

    group_x_student_information = OrderedDict()
    for group, student_x_task_x_task_takens in group_x_student_x_task_takens.iteritems():
        group_x_student_information.setdefault(group, [])

        for student in sorted(student_x_task_x_task_takens.keys(),
                              key=lambda x: u"{0} {1}".format(x.last_name, x.first_name)):
            if user == student:
                user_is_attended = True
            elif not course.user_can_see_transcript(user, student):
                continue

            mark_id, course_mark, course_mark_int = get_course_mark(course, student)

            group_x_student_information[group].append((student,
                                                       student_x_task_x_task_takens[student][0],
                                                       student_x_task_x_task_takens[student][1],
                                                       mark_id,
                                                       course_mark,
                                                       course_mark_int))

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
        'visible_attendance_log': course.user_can_see_attendance_log(request.user),
        'visible_hide_button': Task.objects.filter(Q(course=course) & Q(is_hidden=True)).exists(),
        'show_hidden_tasks': show_hidden_tasks,
        'visible_hide_button_users': len(academ_students),
        'show_academ_users': show_academ_users

    }

    return context


def get_tasklist_context(request, course):
    return tasklist_shad_cpp(request, course)


def get_course_mark(course, student):
    mark_id = -1
    course_mark = '--'
    course_mark_int = -1
    course_marks = course.mark_system

    if course_marks and course_marks.marks:
        if course_marks.marks.all()[0].name_int != -1:
            course_mark_int = -10
        try:
            student_course_mark = StudentCourseMark.objects.get(course=course, student=student)
            if student_course_mark.mark:
                mark_id = student_course_mark.mark.id
                course_mark = unicode(student_course_mark)
                course_mark_int = student_course_mark.mark.name_int
        except StudentCourseMark.DoesNotExist:
            pass

    return mark_id, course_mark, course_mark_int


def courses_list(request, year=None):
    if year is None:
        year_object = get_current_year()
    else:
        year_object = get_object_or_404(Year, start_year=year)

    if year_object is None:
        raise Http404

    courses_list = Course.objects.filter(year=year_object).order_by('name')

    context = {
        'courses_list': courses_list,
        'year': year_object,
    }

    return render(request, 'course_list.html', context)


@require_http_methods(['POST'])
@login_required
def edit_course_information(request):
    user = request.user

    for key in ['course_id', 'course_information']:
        if key not in request.POST:
            raise PermissionDenied

    try:
        course_id = int(request.POST['course_id'])
        course_information = request.POST['course_information'].strip()
    except ValueError:  # not int
        raise PermissionDenied

    course = get_object_or_404(Course, id=course_id)

    if not course.user_can_edit_course(user):
        raise PermissionDenied

    if course_information and not course_information.startswith(u'<div class="not-sanitize">'):
        course_information = u'<div class="not-sanitize">' + course_information + u'</div>'
    course.information = course_information
    course.save()

    return HttpResponse(json.dumps({'info': course_information}),
                        content_type="application/json")


@require_http_methods(['POST'])
@login_required
def set_spectial_course_attend(request):
    user = request.user

    try:
        course_id = int(request.POST['course_id'])
        action = request.POST['action']
    except ValueError:  # not int
        raise PermissionDenied

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


@require_http_methods(['GET', 'POST'])
@login_required
def course_settings(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not course.user_is_teacher(request.user):
        raise PermissionDenied

    schools = course.school_set.all()

    tasks_with_contest = {}
    if course.is_contest_integrated():
        for task in course.task_set.filter(contest_integrated=True, is_hidden=False):
            tasks_with_contest[task.contest_id] = tasks_with_contest.get(task.contest_id, list()) + [task]

    context = {'course': course,
               'visible_queue': course.user_can_see_queue(request.user),
               'visible_attendance_log': course.user_can_see_attendance_log(request.user),
               'user_is_teacher': course.user_is_teacher(request.user),
               'school': schools[0] if schools else '',
               'tasks_with_contest': tasks_with_contest,
               }

    if request.method != "POST":
        form = DefaultTeacherForm(course)
        context['form'] = form
        context['file_extensions'] = get_filename_extensions(course)
        return render(request, 'courses/settings.html', context)

    form = DefaultTeacherForm(course, request.POST)
    context['form'] = form

    if not form.is_valid():
        context['file_extensions'] = get_filename_extensions(course)
        return render(request, 'courses/settings.html', context)

    for group_key, teacher_id in form.cleaned_data.iteritems():
        teacher_id = int(teacher_id)
        group = form.groups[group_key]
        if teacher_id == 0:
            DefaultTeacher.objects.filter(course=course).filter(group=group).delete()
        else:
            teacher = get_object_or_404(User, id=teacher_id)
            default_teacher, _ = DefaultTeacher.objects.get_or_create(course=course, group=group)
            default_teacher.teacher = teacher
            default_teacher.save()

            for issue in Issue.objects.filter(task__course=course, student__group=group, responsible__isnull=True):
                issue.set_teacher(teacher=teacher)

    if 'rb_extensions[]' in request.POST:
        course.filename_extensions = request.POST.getlist('rb_extensions[]')
    else:
        course.filename_extensions.clear()

    course.show_task_one_file_upload = 'show_task_one_file_upload' in request.POST
    course.default_task_send_to_users = 'default_task_send_to_users' in request.POST
    course.default_task_one_file_upload = 'default_task_one_file_upload' in request.POST
    course.show_accepted_after_contest_ok = 'show_accepted_after_contest_ok' in request.POST
    course.default_accepted_after_contest_ok = 'default_accepted_after_contest_ok' in request.POST
    course.show_contest_run_id = 'show_contest_run_id' in request.POST

    redirect_page = None
    if course.has_attendance_log and 'has_attendance_log' not in request.POST:
        redirect_page = '/course/%d' % course.id
    course.has_attendance_log = 'has_attendance_log' in request.POST

    course.save()
    return HttpResponse(json.dumps({'redirect_page': redirect_page}), content_type="application/json")


@require_http_methods(['POST'])
@login_required
def change_visibility_hidden_tasks(request):
    course = get_object_or_404(Course, id=int(request.POST['course_id']))
    if not course.user_is_teacher(request.user):
        raise PermissionDenied

    session_var_name = str(request.user.id) + '_' + request.POST['course_id'] + '_show_hidden_tasks'
    request.session[session_var_name] = not request.session.get(session_var_name, False)

    return HttpResponse("OK")


@require_http_methods(['POST'])
@login_required
def change_visibility_academ_users(request):
    course = get_object_or_404(Course, id=int(request.POST['course_id']))
    if not course.user_is_teacher(request.user):
        raise PermissionDenied

    session_var_name = str(request.user.id) + '_' + request.POST['course_id'] + '_show_academ_users'
    request.session[session_var_name] = not request.session.get(session_var_name, True)

    return HttpResponse("OK")


@require_http_methods(['POST'])
@login_required
def set_course_mark(request):
    user = request.user

    course = get_object_or_404(Course, id=request.POST['course_id'])
    if not course.user_is_teacher(user):
        raise PermissionDenied

    student = get_object_or_404(User, id=request.POST['student_id'])
    if request.POST['mark_id'] != '-1':
        mark = get_object_or_404(MarkField, id=request.POST['mark_id'])
    else:
        mark = MarkField()

    student_course_mark = StudentCourseMark()
    try:
        student_course_mark = StudentCourseMark.objects.get(course=course, student=student)
    except StudentCourseMark.DoesNotExist:
        student_course_mark.course = course
        student_course_mark.student = student

    student_course_mark.teacher = user
    student_course_mark.update_time = datetime.datetime.now()
    student_course_mark.mark = mark
    student_course_mark.save()
    return HttpResponse(json.dumps({'mark': unicode(mark), 'mark_id': mark.id, 'mark_int': mark.name_int}),
                        content_type="application/json")


@require_http_methods(['POST'])
@login_required
def set_task_mark(request):
    task_id = request.POST['task_id']
    task = get_object_or_404(Task, id=task_id)
    if not task.course.user_is_teacher(request.user):
        raise PermissionDenied

    issue, created = Issue.objects.get_or_create(task_id=task_id, student_id=request.POST['student_id'])

    mark = 0
    if request.POST['mark_value'] == '-':
        issue.set_status_new()
    else:
        mark = float(request.POST['mark_value'])
        if mark <= 0:
            issue.set_status_rework()
        else:
            issue.set_status_accepted()

    issue.set_byname('mark', mark)

    return HttpResponse(json.dumps({'mark': mark,
                                    'color': issue.status_field.color}),
                        content_type="application/json")


@require_http_methods(['POST'])
@login_required
def change_table_tasks_pos(request):
    course = get_object_or_404(Course, id=int(request.POST['course_id']))
    if not course.user_is_teacher(request.user):
        raise PermissionDenied

    group = get_object_or_404(Group, id=int(request.POST['group_id']))
    deleting_ids_from_groups = json.loads(request.POST['deleting_ids_from_groups'])
    if deleting_ids_from_groups:
        for task_id, group_ids in deleting_ids_from_groups.iteritems():

            group_ids = list(set(group_ids))
            task = get_object_or_404(Task, id=int(task_id))
            task_groups = task.groups.filter(id__in=group_ids)
            if task.type == task.TYPE_SEMINAR:
                children_groups = reduce(lambda x, y: x + y,
                                         [list(child.groups.all()) for child in task.children.all()], [])
                if set(children_groups).intersection(task_groups):
                    raise PermissionDenied
            else:
                for tg in task_groups:
                    if Issue.objects.filter(task=task, student__in=tg.students.all()).count():
                        raise PermissionDenied
            task.groups.remove(*task.groups.filter(id__in=group_ids))
            task.save()

            for task_relations in TaskGroupRelations.objects.filter(task=task, group__id__in=group_ids):
                task_relations.deleted = True
                task_relations.save()

    if 'task_deleted[]' in request.POST:
        task_deleted = map(lambda x: int(x), dict(request.POST)['task_deleted[]'])
        for task in Task.objects.filter(id__in=task_deleted):
            if task.type == task.TYPE_SEMINAR and not task.children.exists():
                Issue.objects.filter(task=task).delete()

            if not Issue.objects.filter(task=task).count():
                try:
                    task.delete()
                    TaskGroupRelations.objects.get(task=task, group=group).delete()
                except TaskGroupRelations.DoesNotExist:
                    pass
            else:
                raise PermissionDenied

    if 'task_order[]' in request.POST:
        task_order = map(lambda x: int(x), dict(request.POST)['task_order[]'])

        for task_relations in TaskGroupRelations.objects.select_related('task') \
                .filter(task__id__in=task_order).filter(group=group):
            task_relations.position = task_order.index(task_relations.task.id)
            task_relations.save()

    return HttpResponse("OK")


@require_http_methods(['POST'])
@login_required
def ajax_update_contest_tasks(request):
    user = request.user
    if not request.is_ajax():
        raise PermissionDenied

    if 'tasks_with_contest[]' not in request.POST or 'contest_id' not in request.POST:
        raise PermissionDenied

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
                response['error'] = _(u'kontesta_ne_sushestvuet')
            else:
                response['error'] = _(u'oshibka_kontesta') + ' ' + problem_req['error']['message']
        if 'result' in problem_req.json():
            problems = problem_req.json()['result']['problems']

        contest_responses = [contest_info, problems]
    else:
        response['is_error'] = True
        if "You're not allowed to view this contest." in contest_info:
            response['error'] = _(u"net_prav_na_kontest")
        elif "Contest with specified id does not exist." in contest_info:
            response['error'] = _(u'kontesta_ne_sushestvuet')
        else:
            response['error'] = _(u'oshibka_kontesta') + contest_info

    if not response['is_error']:
        for task in Task.objects.filter(id__in=dict(request.POST)['tasks_with_contest[]']):
            alias = task.problem_id
            if contest_id != task.contest_id:
                continue

            for problem in contest_responses[0]['problems']:
                if problem['alias'] == alias:
                    task.title = problem['problemTitle']
                    task.task_text = problem['statement']
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

            reversion.set_user(user)
            reversion.set_comment("Update from contest")

            response['tasks_title'][task.id] = task.get_title(user.profile.language)

    return HttpResponse(json.dumps(response),
                        content_type="application/json")


@require_http_methods(['POST'])
@login_required
def ajax_rejudge_contest_tasks(request):
    if not request.is_ajax():
        raise PermissionDenied

    if 'tasks_with_contest[]' not in request.POST:
        raise PermissionDenied

    for issue in Issue.objects.filter(task_id__in=dict(request.POST)['tasks_with_contest[]']):
        contest_rejudge(issue)

    return HttpResponse("OK")


def attendance_list(request, course, group=None):
    user = request.user
    user_is_attended = False
    user_is_attended_special_course = False
    show_academ_users = request.session.get("%s_%s_show_academ_users" % (request.user.id, course.id), True)
    msk_time = convert_datetime(localtime(now()), user.profile.time_zone)

    course.can_edit = course.user_can_edit_course(user)
    if course.can_be_chosen_by_extern:
        course.groups.add(course.group_with_extern)

    if group:
        groups = [group]
    else:
        groups = course.groups.all().order_by('name')

    group_x_student_x_lessons = OrderedDict()
    group_x_lesson_list = {}
    group_inactive_lessons = {}
    default_teacher = {}

    academ_students = []

    for group in groups:
        group_x_lesson_list[group] = Lesson.objects.filter(course=course, group=group).order_by('position')
        group_inactive_lessons[group] = Lesson.objects.filter(course=course,
                                                              group=group,
                                                              date_starttime__gt=msk_time
                                                              ).order_by('position')
        active_lessons_count = len(group_x_lesson_list[group]) - len(group_inactive_lessons[group])

        students = group.students.filter(is_active=True)
        not_active_students = UserProfile.objects.filter(Q(user__in=group.students.filter(is_active=True))
                                                         & (Q(user_status__tag='not_active')
                                                            | Q(user_status__tag='academic')))
        academ_students += [x.user for x in not_active_students]
        if not show_academ_users:
            students = set(students) - set(academ_students)

        students_x_lessons = {}

        for student in students:
            if user == student:
                user_is_attended = True
                user_is_attended_special_course = True

            not_visited_lessons = []
            for lssn in group_x_lesson_list[group][:active_lessons_count]:
                if student in lssn.not_visited_students.all():
                    not_visited_lessons.append(lssn)
            students_x_lessons[student] = not_visited_lessons, active_lessons_count - len(not_visited_lessons)

        group_x_student_x_lessons[group] = students_x_lessons

        try:
            default_teacher[group] = DefaultTeacher.objects.get(course=course, group=group).teacher
        except DefaultTeacher.DoesNotExist:
            default_teacher[group] = None
    group_x_student_information = OrderedDict()
    for group, students_x_lessons in group_x_student_x_lessons.iteritems():
        group_x_student_information.setdefault(group, [])

        for student in sorted(students_x_lessons.keys(),
                              key=lambda x: u"{0} {1}".format(x.last_name, x.first_name)):
            if user == student:
                user_is_attended = True
            elif not course.user_can_see_transcript(user, student):
                continue

            group_x_student_information[group].append((student,
                                                       students_x_lessons[student][0], students_x_lessons[student][1]))
    context = {
        'course': course,
        'group_information': group_x_student_information,
        'group_lessons': group_x_lesson_list,
        'group_inactive_lessons': group_inactive_lessons,
        'default_teacher': default_teacher,
        'user': user,
        'user_is_attended': user_is_attended,
        'user_is_attended_special_course': user_is_attended_special_course,
        'user_is_teacher': course.user_is_teacher(user),
        'visible_hide_button_users': len(academ_students),
        'show_academ_students': show_academ_users
    }

    return context


@require_http_methods(['GET'])
@login_required
def attendance_page(request, course_id, group_id=None):
    user = request.user
    if not user.profile.is_active():
        raise PermissionDenied

    course = get_object_or_404(Course, id=course_id)
    if not course.user_can_see_attendance_log(request.user):
        raise PermissionDenied

    if group_id:
        group = get_object_or_404(Group, id=group_id)
    else:
        group = None

    schools = course.school_set.all()

    attendance_context = attendance_list(request, course, group)

    context = attendance_context
    context['lssnlist_template'] = 'courses/attendance_list.html'
    context['group_attendance_list'] = bool(group)
    context['school'] = schools[0] if schools else ''
    context['show_academ_users'] = request.session.get(
        str(request.user.id) + '_' + str(course.id) + '_show_academ_users', True)
    context['full_width_page'] = True

    return render(request, 'courses/attendance.html', context)


@require_http_methods(['POST'])
@login_required
def lesson_visited(request):
    lesson_id = request.POST['lssn_id']
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not lesson.course.user_is_teacher(request.user):
        raise PermissionDenied
    if lesson.date_starttime.date() > datetime.datetime.today().date():
        raise PermissionDenied
    student = User.objects.get(id=request.POST['student_id'])
    if 'lesson_visited' in request.POST:
        value = 1
        lesson.not_visited_students.remove(student)
    else:
        value = -1
        lesson.not_visited_students.add(student)
    lesson.save()

    can_be_deleted = lesson.group.students.count() - lesson.not_visited_students.count()
    return HttpResponse(json.dumps({'visited': value, 'lesson_id': lesson_id,
                                    'deleted': can_be_deleted}),
                        content_type="application/json")


@login_required
def lesson_delete(request):
    if request.method != 'POST':
        raise PermissionDenied

    lesson_id = request.POST['lesson_id']
    delete_all = request.POST['delete_all'] == 'true'
    lesson = get_object_or_404(Lesson, id=lesson_id)
    student_ids = lesson.group.students.values_list('id', flat=True)
    students_x_lesson_diff = {}

    if not delete_all:
        deleted_ids = [lesson_id]
        students_not_visited = lesson.not_visited_students.values_list('id', flat=True)
        if lesson.date_starttime <= now():
            students_x_lesson_diff = {stud: 1 for stud in student_ids if stud not in students_not_visited}
        lesson.delete()
    else:
        schedule_id = lesson.schedule_id
        count_lessons_inactive = Lesson.objects.filter(
            schedule_id=schedule_id,
            date_starttime__gte=max(now(), lesson.date_starttime)
        ).count()

        lessons_to_del = Lesson.objects.filter(
            schedule_id=schedule_id,
            date_starttime__gte=lesson.date_starttime
        ).order_by('position')

        students_x_lesson_diff = {stud: len(lessons_to_del) - count_lessons_inactive for stud in student_ids}
        deleted_ids = []
        students_not_visited = []
        for lssn in lessons_to_del:
            students_not_visited += lssn.not_visited_students.values_list('id', flat=True)
            deleted_ids.append(lssn.id)
            lssn.delete()
        count_not_visited_students = Counter(students_not_visited)
        for stud in student_ids:
            students_x_lesson_diff[stud] -= count_not_visited_students[stud]

    return HttpResponse(json.dumps({'deleted': deleted_ids,
                                    'students_lesson_diff': students_x_lesson_diff.items()}),
                        content_type="application/json")


def view_statistic(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if course.is_python_task:
        return pythontask.python_stat(request, course)
