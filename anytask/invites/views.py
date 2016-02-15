from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import Http404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.conf import settings

import datetime

from invites.models import Invite 
from groups.models import Group
from years.common import get_current_year

def generate_invites(request):
    user = request.user
    
    if not Invite.user_can_generate_invite(user):
        return render_to_response('generate_forbidden.html', {}, context_instance=RequestContext(request)) 
    
    if request.method == 'POST':
        return generate_invites_post(request)
    
    
    groups = Group.objects.filter(year=get_current_year())
    courses = Course.objects.filter(is_active=True)
    
    context = {
        'groups'    : groups,
        'courses'   : courses,
    }
    
    return render_to_response('generate.html', context, context_instance=RequestContext(request))

def generate_invites_post(request):
    user = request.user
    
    if 'number_of_invites' not in request.POST:
        return HttpResponseForbidden()
    
    #invites_not_for_group = False
    #if 'invites_not_for_group' in request.POST:
    #    invites_not_for_group = True
    
    group_id = None
    if 'group_id' in request.POST:
        try:
            group_id = int(request.POST['group_id'])
        except ValueError: #not int
            return HttpResponseForbidden()
    if 'course_id' in request.POST:
        try:
            group_id = int(request.POST['course_id'])
        except ValueError: #not int
            return HttpResponseForbidden()
    #if invites_not_for_group == False and group_id is None:
    #    return HttpResponseForbidden()
    
    try:
        number_of_invites = int(request.POST['number_of_invites'])
    except ValueError: #not int
        return HttpResponseForbidden()
    
    group = None
    #if not invites_not_for_group:
    group = get_object_or_404(Group, id = group_id)
    
    invites = Invite.generate_invites(number_of_invites, user, group)
    invite_expired_date = datetime.date.today() + datetime.timedelta(days=settings.INVITE_EXPIRED_DAYS)

    context = {
        'invites'               : invites,
        'group'                 : group, 
        'invite_expired_date'   : invite_expired_date,
    }
    
    return render_to_response('invites_list.html', context, context_instance=RequestContext(request))
