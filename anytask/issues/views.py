# -*- coding: utf-8 -*-
import pprint
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from issues.forms import FileForm
from issues.models import Issue, Event, upload_review
from issues.model_issue_field import IssueField


def user_is_teacher_or_staff(user, issue):
    if user.is_staff:
        return True
    if issue.task.course.user_is_teacher(user):
        return True
    return False

def user_can_read(user, issue):
    if user.is_staff:
        return True
    if user == issue.student:
        return True
    if issue.task.course.user_is_teacher(user):
        return True

    return False


def prepare_info_fields(info_fields, request, issue):
    user = request.user
    for field in info_fields:
        field.editable = field.can_edit(user, issue)
        if field.is_visible():
            field.repr = issue.get_field_repr(field)

        field.value = issue.get_field_value_for_form(field)

        data = { field.name : field.value }
        field.form = field.get_form(request, issue, data)

def upload_to_rb(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    upload_review(event)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])

@csrf_exempt
def message_from_rb(request, review_id):
    field = get_object_or_404(IssueField, name='review_id')
    events = list(Event.objects.filter(field_id=field.id))
    for event in events:
        if event.issue.get_byname('review_id') == review_id:
            issue = event.issue
            break

    if request.method == 'POST':
        value = u'<strong>Добавлен новый комментарий в <a href="{1}/r/{0}">Review \
                  request {0}</a>'.format(review_id,settings.RB_API_URL)+': \n'
        if request.POST.get('diff-url',0):
            value += u'<a href="{0}">Комментарий к коду</a> '.format(settings.RB_API_URL+request.POST.get('diff-url',''))
        value += request.POST.get('diff','')
        value += request.POST.get('body_top','') 
        value += request.POST.get('body_bottom','')
        field = get_object_or_404(IssueField, name='comment')
        author = get_object_or_404(User, username=request.POST.get('author',''))
        event = issue.create_event(field, author=author)
        event.value = value
        event.save()
        issue.save()
        return HttpResponse(status=201)

@login_required
def issue_page(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)
    if not user_can_read(request.user, issue):
        raise PermissionDenied

    issue_fields = issue.task.course.issue_fields.all()

    if request.method == 'POST':
        form_name = request.POST['form_name']

        for field in issue_fields:
            if form_name == u'{0}_form'.format(field.name):
                form = field.get_form(request, issue)

                if form.is_valid():
                    value = form.cleaned_data[field.name]
                    if field.name == 'comment':
                        value = {
                            'comment': value,
                            'files': request.FILES.getlist('files')
                        }

                    issue.set_field(field, value, request.user)
                    return HttpResponseRedirect('')

    prepare_info_fields(issue_fields, request, issue)

    context = {
        'issue': issue,
        'issue_fields': issue_fields,
        'course': issue.task.course,
        'events_to_show': 7,
        'teacher_or_staff': user_is_teacher_or_staff(request.user, issue),
    }

    return render_to_response('issues/issue.html', context, context_instance=RequestContext(request))


@login_required
def get_or_create(request, task_id, student_id):
    if not request.is_ajax():
        return HttpResponseForbidden()

    issue, created = Issue.objects.get_or_create(task_id=task_id, student_id=student_id)

    data = {
        'issue_url': issue.get_absolute_url(),
    }

    return HttpResponse(json.dumps(data), content_type='application/json')
