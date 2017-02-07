from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import Http404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect
from django.conf import settings

import datetime

from invites.models import Invite 
from groups.models import Group
from years.common import get_current_year
from courses.models import Course

from users.forms import InviteActivationForm

def generate_invites(request):
    user = request.user

    if not Invite.user_can_generate_invite(user):
        return render_to_response('generate_forbidden.html', {}, context_instance=RequestContext(request)) 

    if request.method == 'POST':
        return generate_invites_post(request)

    courses = Course.objects.filter(is_active=True)
    groups = Group.objects.filter(year=get_current_year())
    true_courses = []
    for course in courses:
        if user in course.teachers.all():
            true_courses.append(course)

    groups = groups.filter(course__in=true_courses).distinct().order_by('name')

    context = {
        'groups'    : groups,
        #'courses'   : courses,
    }
    
    return render_to_response('generate.html', context, context_instance=RequestContext(request))

def generate_invites_post(request):
    user = request.user
    
    if 'number_of_invites' not in request.POST:
        return HttpResponseForbidden()
    
    group_id = None
    if 'group_id' in request.POST:
        try:
            group_id = int(request.POST['group_id'])
        except ValueError: #not int
            return HttpResponseForbidden()

    #if invites_not_for_group == False and group_id is None:
    #    return HttpResponseForbidden()
    
    try:
        number_of_invites = int(request.POST['number_of_invites'])
    except ValueError: #not int
        return HttpResponseForbidden()
    
    group = None

    group = get_object_or_404(Group, id = group_id)
    
    invites = Invite.generate_invites(number_of_invites, user, group)
    invite_expired_date = datetime.date.today() + datetime.timedelta(days=settings.INVITE_EXPIRED_DAYS)

    context = {
        'invites'               : invites,
        'group'                 : group, 
        'invite_expired_date'   : invite_expired_date,
    }
    
    return render_to_response('invites_list.html', context, context_instance=RequestContext(request))   
