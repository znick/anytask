# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from issues.models import Issue, Event
from issues.model_issue_field import IssueField


@csrf_exempt
def message_from_rb(request, review_id):
    field = get_object_or_404(IssueField, name='review_id')
    for event in Event.objects.filter(field_id=field.id):
        if event.issue.get_byname('review_id') == review_id:
            issue = event.issue
            break

    if request.method == 'POST':
        value = {'files':[], 'comment':''}
        value = u'<strong>Добавлен новый комментарий в <a href="{1}/r/{0}">Review\
                  request {0}</a>'.format(review_id,settings.RB_API_URL)+'. \n'
        #if request.POST.get('diff-url',0):
        #    value += u'<a href="{0}">Комментарий к коду</a> '.format(settings.RB_API_URL+request.POST.get('diff-url',''))
        #value += request.POST.get('diff','')
        #value += request.POST.get('body_top','')
        #value += request.POST.get('body_bottom','')
        field = get_object_or_404(IssueField, name='comment')
        author = get_object_or_404(User, username=request.POST.get('author',''))
        #event = issue.create_event(field, author=author)
        #event.value = value
        #event.save()
        issue.set_byname('comment', value, author)
        issue.save()
        return HttpResponse(status=201)
