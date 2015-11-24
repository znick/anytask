# -*- coding: utf-8 -*-
import pprint
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
import json
from django.conf import settings
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
                    if 'Me' in request.POST:
                        if field.name == 'responsible_name':
                            value = request.user
                        else:
                            if request.user not in value:
                                value.append(request.user)
                    if 'Accepted' in request.POST:
                        issue.set_byname('status', 'accepted')

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
    #if not request.is_ajax():
    #    return HttpResponseForbidden()

    issue, created = Issue.objects.get_or_create(task_id=task_id, student_id=student_id)

    data = {
        'issue_url': issue.get_absolute_url(),
    }

    return HttpResponseRedirect("/issue/"+str(issue.id))#(json.dumps(data), content_type='application/json')
