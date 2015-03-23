from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.db.models import Q
from django.conf import settings
from django.http import Http404
from django.contrib.auth.decorators import login_required

from users.models import UserProfile
from django.contrib.auth.models import User
from tasks.models import TaskTaken
from years.models import Year
from groups.models import Group
from cources.models import Cource
from invites.models import Invite

from years.common import get_current_year

import datetime
import operator

@login_required
def profile(request, username=None, year=None):
    user = request.user

    user_to_show = user
    if username:
        user_to_show = get_object_or_404(User, username=username)

    if year:
        current_year = get_object_or_404(Year, start_year=year)
    else:
        current_year = get_current_year()

    tasks_taken = TaskTaken.objects.filter(user=user_to_show).filter(Q( Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED))).filter(task__cource__is_active=True)

    cource_x_tasks = {}
    cource_x_scores = {}
    for task_taken in tasks_taken:
        cource = task_taken.task.cource
        cource_x_scores.setdefault(cource, 0)
        task_end_date = task_taken.added_time + datetime.timedelta(days=cource.max_days_without_score)
        cource_x_tasks.setdefault(cource, [])
        cource_x_tasks[cource].append((task_taken.task, task_taken.task.score_max, task_taken.score, task_end_date))
        cource_x_scores[cource] += task_taken.score

    user_cource_information = []
    for cource in sorted(cource_x_tasks.keys(), key=lambda x: x.name):
        user_cource_information.append((cource,cource_x_scores[cource],cource_x_tasks[cource]))

    groups = user_to_show.group_set.filter(year=current_year)
    teacher_in_cources = Cource.objects.filter(is_active=True).filter(teachers=user_to_show)
    can_generate_invites = user_to_show == user and Invite.user_can_generate_invite(user)

    context = {
        'user_to_show'              : user_to_show,
        'groups'                    : groups,
        'user_cource_information'   : user_cource_information,
        'teacher_in_cources'        : teacher_in_cources,
        'can_generate_invites'      : can_generate_invites,
    }

    return render_to_response('user_profile.html', context, context_instance=RequestContext(request))

def add_user_to_group(request):
    user = request.user

    if not request.method == 'POST':
        return HttpResponseForbidden()

    if 'group_id' not in request.POST:
        return HttpResponseForbidden()

    try:
        group_id = int(request.POST['group_id'])
    except ValueError:
        return HttpResponseForbidden()

    group = get_object_or_404(Group, id=group_id)
    group.students.add(user)
    group.save()

    return HttpResponse("OK")


