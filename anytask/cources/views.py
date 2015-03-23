#coding: utf-8

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import Http404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.db.models import Q
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth import authenticate
from django.utils.translation import ugettext as _
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.utils import simplejson as json
from django.conf import settings

import datetime

from cources.models import Cource
from groups.models import Group
from tasks.models import TaskTaken, Task
from years.models import Year
from years.common import get_current_year
from cource_statistics import CourceStatistics
from score import TaskInfo
from anysvn.common import svn_log_rev_message, get_svn_external_url, svn_diff
from anysvn.svn import SvnDiff
from anyrb.common import AnyRB
from issues.models import Issue

from common.ordered_dict import OrderedDict

import base64

class HttpResponseUnauthorized(HttpResponse):
    def __init__(self, *args, **kwargs):
        HttpResponse.__init__(self, *args, **kwargs)
        self.status_code = 401
        self["WWW-Authenticate"] = 'Basic realm="AnyTask"'

def tasks_list(request, cource_id):
    cource = get_object_or_404(Cource, id=cource_id)

    if request.GET.get("format") == "json":
        return tasks_list_json(request, cource)

    if cource.private and not cource.user_is_attended(request.user):
        return render_to_response('cource_private_forbidden.html', {"cource" : cource}, context_instance=RequestContext(request))

    if cource.type == Cource.TYPE_POTOK:
        return tasks_list_potok(request, cource)

    if cource.type == Cource.TYPE_ONE_TASK_MANY_GROUP:
        return tasks_list_one_tasks_many_group(request, cource)

    if cource.type == Cource.TYPE_MANY_TASK_MANY_GROUP:
        return tasks_list_many_task_many_group(request, cource)

    if cource.type == Cource.TYPE_SPECTIAL_COURCE:
        if cource.take_policy == Cource.TAKE_POLICY_SELF_TAKEN:
            return tasks_list_potok(request, cource)
        if cource.take_policy == Cource.TAKE_POLICY_ALL_TASKS_TO_ALL_STUDENTS:
            return tasks_list_many_task_many_group(request, cource)

    return


def _group_task_takens_by_task(task_takens):
    task_x_task_takens = {}
    for task_taken in task_takens:
        task = task_taken.task

        task_x_task_takens.setdefault(task, [])
        task_x_task_takens[task].append(task_taken)

    return task_x_task_takens


def tasks_list_one_tasks_many_group(request, cource):
    user = request.user
    user_is_attended = False
    user_is_attended_special_cource = False
    cource.can_edit = cource.user_can_edit_cource(user)
    students_x_tasks = OrderedDict()
    tasks = list(Task.objects.filter(cource=cource).order_by('weight'))

    students = []
    for group in cource.groups.all().order_by('name'):
        for student in group.students.filter(is_active=True):
            if student == user:
                user_is_attended = True
            student.group_for_this_cource = group
            students.append(student)

    user_is_attended = user in students

    students.extend(cource.students.all())

    if not user_is_attended and user in students:
        user_is_attended = True
        user_is_attended_special_cource = True

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

        'cource' : cource,
        'user_is_attended' : user_is_attended,
        'user_is_attended_special_cource' : user_is_attended_special_cource,
    }

    return render_to_response('cource_tasks_one_tasks_many_group.html', context, context_instance=RequestContext(request))


def tasks_list_many_task_many_group(request, cource):
    user = request.user
    user_is_attended = False
    user_is_attended_special_cource = False

    cource.can_edit = cource.user_can_edit_cource(user)

    group_x_student_x_task_takens = OrderedDict()
    group_x_task_list = {}
    group_x_max_score = {}

    task = Task()
    task.is_shown = None
    task.is_hidden = None

    for group in cource.groups.all().order_by('name'):
        student_x_task_x_task_takens = {}

        group_x_task_list[group] = Task.objects.filter(cource=cource).filter(group=group).order_by('weight')
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

            group_x_student_information[group].append((student, student_x_task_x_task_takens[student][0], student_x_task_x_task_takens[student][1]))


    extern_max_score = 0
    extern_student_x_task_takens = {}

    extern_tasks = Task.objects.filter(cource=cource).filter(group=None).order_by('weight')
    for task in extern_tasks:
        task.add_user_properties(user)

        if not task.is_hidden:
            extern_max_score += task.score_max
        if task.task_text is None:
            task.task_text = ''

    task_takens = TaskTaken.objects.filter(task__in=extern_tasks)
    for student in cource.students.all():
        if user == student:
            user_is_attended = True
            user_is_attended_special_cource = True

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
        'cource'        : cource,
        'group_information'   : group_x_student_information,
        'group_tasks'   : group_x_task_list,
        'group_x_max_score' : group_x_max_score,

        'extern_max_score' : extern_max_score,
        'extern_tasks'  : extern_tasks,
        'extern_student_information' : extern_student_information,

        'user' : user,
        'user_is_attended' : user_is_attended,
        'user_is_attended_special_cource' : user_is_attended_special_cource,
    }

    return render_to_response('cource_tasks_many_task_many_group.html', context, context_instance=RequestContext(request))


def tasks_list_potok(request, cource):
    user = request.user

    cource.can_edit = cource.user_can_edit_cource(user)
    delta = datetime.timedelta(days=cource.max_days_without_score)
    task_and_task_taken = []
    for task in Task.objects.filter(cource=cource).filter(parent_task=None).order_by('weight'):
        task.add_user_properties(user)

        if task.task_text is None:
            task.task_text = ''

        task_taken_list = []
        for task_taken in TaskTaken.objects.filter(task=task).exclude(task__is_hidden=True).filter(Q( Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED))):
            if cource.max_days_without_score and task_taken.status == TaskTaken.STATUS_TAKEN:
                task_taken.cancel_date = task_taken.added_time + delta
            task_taken_list.append(task_taken)

        if task.has_subtasks():
            subtask_and_task_takens = []
            for subtask in Task.objects.filter(parent_task=task).order_by('weight'):
                subtask.add_user_properties(user)

                if subtask.task_text is None:
                    subtask.task_text = ''

                subtask_takens = list(TaskTaken.objects.filter(task=subtask).exclude(task__is_hidden=True).exclude(task__parent_task__is_hidden=True).filter(Q( Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED))))
                if cource.max_days_without_score:
                    for subtask_taken in filter(lambda x: x.status == TaskTaken.STATUS_TAKEN, subtask_takens):
                        subtask_taken.cancel_date = subtask_taken.added_time + delta
                subtask_and_task_takens.append((subtask, subtask_takens))
            task_and_task_taken.append((task, subtask_and_task_takens))
        else:
            task_and_task_taken.append((task, task_taken_list))

    context = {
        'cource'        : cource,
        'tasks_taken'   : task_and_task_taken,
        'STATUS_TAKEN'  : TaskTaken.STATUS_TAKEN,
        'STATUS_SCORED' : TaskTaken.STATUS_SCORED,
    }

    return render_to_response('cource_tasks_potok.html', context, context_instance=RequestContext(request))


def tasks_list_json_try_basic_auth(request):
    if 'HTTP_AUTHORIZATION' not in request.META:
        return AnonymousUser()

    auth_str = request.META['HTTP_AUTHORIZATION']
    auth_str_parts = auth_str.split()

    if auth_str_parts[0] != "Basic":
        return AnonymousUser()

    username, password = base64.b64decode(auth_str_parts[1]).split(":", 1)
    user = authenticate(username=username, password=password)
    if user is None:
        return AnonymousUser()
    return user


def tasks_list_json(request, cource):
    user = request.user
    if user.is_anonymous():
        user = tasks_list_json_try_basic_auth(request)
    if user.is_anonymous():
        return HttpResponseUnauthorized()

    ret = {
        "course_id"         : cource.id,
        "course_name"       : cource.name,
        "course_name_id"    : cource.name_id,
        "information"       : cource.information,
        "year"              : cource.year.start_year,
        "is_active"         : cource.is_active,
        "type"              : cource.type,
        "take_policy"       : cource.take_policy,
    }

    tasks = []
    for task_obj in Task.objects.filter(cource=cource):
        task = {
            "task_id"        : task_obj.id,
            "title"          : task_obj.title,
            "parent_task_id" : task_obj.parent_task_id,
            "score_max"      : task_obj.score_max,
        }

        if task_obj.group:
            task["group"] = task_obj.group.name

        students = []
        for task_taken in TaskTaken.objects.filter(task=task_obj):
            student = {
                "username"  : task_taken.user.username,
                "user_name" : task_taken.user.get_full_name(),
                "status"    : task_taken.status,
                "score"     : task_taken.score,
                "scored_by" : None,
                "svn"       : None,
            }

            if task_taken.scored_by:
                student["scored_by"] = task_taken.scored_by.username

            issue = None
            try:
                issue = Issue.objects.filter(task=task_obj, student=task_taken.user).order_by('-update_time')[0]
            except Issue.DoesNotExist:
                pass
            except IndexError:
                pass

            if issue:
                student["svn"] = {
                    "rb_review_id"  : issue.rb_review_id,
                    "svn_rev"       : issue.svn_commit_id,
                    "svn_path"      : issue.svn_path,
                }


            students.append(student)

        task["students"] = students
        tasks.append(task)
    ret["tasks"] = tasks

    response = HttpResponse(content_type="application/json")
    json.dump(ret, response, indent=4)
    return response


def get_task(request, cource_id, task_id):
    user = request.user

    task = get_object_or_404(Task, id=task_id)
    user_can_take_task, reason = task.user_can_take_task(user)
    if user_can_take_task:
        task_taken, _ = TaskTaken.objects.get_or_create(user=user, task=task)
        task_taken.status = TaskTaken.STATUS_TAKEN
        task_taken.save()

    return redirect(tasks_list, cource_id=cource_id)

def cancel_task(request, cource_id, task_id):
    user = request.user

    task = get_object_or_404(Task, id=task_id)

    if task.user_can_cancel_task(user):
        task_taken = get_object_or_404(TaskTaken, user=user, task=task)
        task_taken.status = TaskTaken.STATUS_CANCELLED
        task_taken.save()

    return redirect(tasks_list, cource_id=cource_id)

def score_task(request):
    user = request.user

    if not request.method == 'POST':
        return HttpResponseForbidden()

    for key in ['task_id', 'student_id', 'score', 'comment']:
        if key not in request.POST:
            return HttpResponseForbidden()

    try:
        task_id = int(request.POST['task_id'])
        student_id = int(request.POST['student_id'])
        score = int(request.POST['score'])
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

    for key in ['task_id', 'task_title', 'task_text', 'max_score']:
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
    except ValueError: #not int
        return HttpResponseForbidden()

    task = get_object_or_404(Task, id = task_id)

    if not task.cource.user_is_teacher(user):
        return HttpResponseForbidden()

    task.is_hidden = hidden_task
    if task.parent_task:
        if task.parent_task.is_hidden:
            task.is_hidden = True

    task.title = task_title
    task.task_text = task_text
    task.score_max = max_score
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

    for key in ['cource_id', 'group_id', 'parent_id', 'task_title', 'task_text', 'max_score']:
        if key not in request.POST:
            return HttpResponseForbidden()

    hidden_task = False
    if 'hidden_task' in request.POST:
        hidden_task = True

    try:
        cource_id = int(request.POST['cource_id'])
        task_title = request.POST['task_title'].strip()
        task_text = request.POST['task_text'].strip()
        max_score = int(request.POST['max_score'])

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

    cource = get_object_or_404(Cource, id = cource_id)
    group = None
    if group_id is not None:
        group = get_object_or_404(Group, id = group_id)
    parent = None
    if parent_id is not None:
        parent = get_object_or_404(Task, id = parent_id)

    if not cource.user_can_edit_cource(user):
        return HttpResponseForbidden()

    max_weight_query = Task.objects.filter(cource=cource)
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
    task.cource = cource
    task.group = group
    task.parent_task = parent
    task.weight = max_weight
    task.title = task_title
    task.task_text = task_text
    task.score_max = max_score
    task.is_hidden = hidden_task
    task.updated_by = user
    task.save()

    return HttpResponse("OK")


def cources_list(request, year=None):
    if year is None:
        year_object = get_current_year()
    else:
        year_object = get_object_or_404(Year, start_year=year)

    if year_object is None:
        raise Http404

    cources_list = Cource.objects.filter(year=year_object).order_by('name')

    context = {
        'cources_list'  : cources_list,
        'year'  : year_object,
    }

    return render_to_response('course_list.html', context, context_instance=RequestContext(request))

def cource_statistics(request, cource_id):
    cource = get_object_or_404(Cource, id = cource_id)
    cource_tasks = Task.objects.filter(cource=cource).exclude(is_hidden=True)

    statistics = CourceStatistics(cource_tasks)

    for group in cource.groups.all().order_by('name'):
        statistics.update(group)

    context = {
        'cource'            : cource,
        'groups_statistics'  : statistics.get_groups_statistics(),
        'cource_statistics' : statistics.get_cource_statistics(),
    }

    return render_to_response('statistics.html', context, context_instance=RequestContext(request))

def tasks_description(request, cource_id):
    cource = get_object_or_404(Cource, id = cource_id)

    group_x_tasks = {}
    cource_tasks = []
    if cource.type == Cource.TYPE_MANY_TASK_MANY_GROUP:
        for group in cource.groups.all():
            group_x_tasks[group] = Task.objects.filter(cource=cource).filter(group=group).exclude(is_hidden=True).order_by('weight')

        cource_tasks = Task.objects.filter(cource=cource).filter(group=None).exclude(is_hidden=True).order_by('weight')
    else:
        cource_tasks = Task.objects.filter(cource=cource).exclude(is_hidden=True).order_by('weight')

    context = {
        'cource'            : cource,
        'group_x_tasks'     : group_x_tasks,
        'cource_tasks'      : cource_tasks,
    }

    return render_to_response('course_tasks_description.html', context, context_instance=RequestContext(request))

def edit_cource_information(request):
    user = request.user

    if not request.method == 'POST':
        return HttpResponseForbidden()

    for key in ['cource_id', 'cource_information']:
        if key not in request.POST:
            return HttpResponseForbidden()

    try:
        cource_id = int(request.POST['cource_id'])
        cource_information = request.POST['cource_information'].strip()
    except ValueError: #not int
        return HttpResponseForbidden()

    cource = get_object_or_404(Cource, id = cource_id)

    if not cource.user_can_edit_cource(user):
        return HttpResponseForbidden()

    cource.information = cource_information
    cource.save()

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

    cource = get_object_or_404(Cource, id=course_id)
    if cource.type != Cource.TYPE_SPECTIAL_COURCE:
        return HttpResponseForbidden()

    if action == "add":
        cource.students.add(user)

    if action == "remove":
        cource.students.remove(user)

    return HttpResponse("OK")

class SubmitReview(View):
    @method_decorator(login_required)
    def dispatch(self, request, task_id, *args, **kwargs):
        user = request.user
        task = get_object_or_404(Task, id=task_id)

        if not task.user_can_pass_task(user):
            return HttpResponseForbidden()

        context = {"task" : task}

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
                descriptions.append(u"{0:3} {1:20} {2} {3}".format(*log))

        return "\n".join(descriptions).encode("utf-8")


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
        issue.svn_path = svn_path

        summary = u"[{0}][{1}] {2}".format(user.get_full_name(), task.cource.get_user_group(user), task.title)

        review_group_name = settings.RB_API_DEFAULT_REVIEW_GROUP
        if task.cource.name_id:
            review_group_name =  "teachers_{0}".format(task.cource.name_id)
        else:
            try:
                review_group_name = "teachers_{0}".format(task.cource.name)
            except Exception:
                pass


        review_group_name = review_group_name.replace(".", "_")
        review_group_name = review_group_name.replace("/", "_")
        review_group_name = review_group_name.lower()

        anyrb = AnyRB()

        description = self._get_description(request, task, svn_path, rev_a, rev_b)
        try:
            diff_content = svn_diff(user, path=svn_path)
        except SvnDiff.MaxSizeError:
            return render_to_response('submit_review_diff_too_big.html', {}, context_instance=RequestContext(request))
        review_id = anyrb.submit_review(user, diff_content, summary=summary, description=description, review_group_name=", ".join((review_group_name, settings.RB_API_DEFAULT_REVIEW_GROUP)),  path=svn_path, review_id=review_id)

        issue.rb_review_id = review_id
        issue.save()

        context = {
            'review_url' : anyrb.get_review_url(request, review_id),
            'task' : task,
        }

        return render_to_response('submit_review_done.html', context, context_instance=RequestContext(request))

    def _get_submit_form(self, request, task, svn_path):
        user = request.user

        logs = list(svn_log_rev_message(user, svn_path))

        if not logs:
            return render_to_response('submit_review_no_such_path.html', {}, context_instance=RequestContext(request))

        rev_a = logs[0][0]
        rev_b = logs[-1][0]

        context = {
            "ready_to_submit" : 1,
            "rev_a" : rev_a,
            "rev_b" : rev_b,
            "logs" : logs,
            "task" : task,
        }

        return render_to_response('submit_review_form.html', context, context_instance=RequestContext(request))


    @method_decorator(login_required)
    def dispatch(self, request, task_id, svn_path="", *args, **kwargs):
        task = get_object_or_404(Task, id=task_id)

        if request.method == "POST":
            return self._submit_review(request, task, svn_path)

        return self._get_submit_form(request, task, svn_path)
