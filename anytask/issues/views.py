# -*- coding: utf-8 -*-
import pprint
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
import json
import os   
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from issues.forms import FileForm
from issues.models import Issue, Event, File
from issues.model_issue_field import IssueField

from django.core.urlresolvers import reverse
from django.views import generic
from django.views.decorators.http import require_POST
from jfu.http import upload_receive, UploadResponse, JFUResponse

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

                    if field.name in ['mark','status', 'responsible_name', 'followers_names']:
                        if not user_is_teacher_or_staff(request.user, issue):
                            raise PermissionDenied
    
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
                        if 'need_info' in request.POST:
                            issue.set_byname('status', 'need_info')
        
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


@require_POST
def upload(request, issue_id):

    # The assumption here is that jQuery File Upload
    # has been configured to send files one at a time.
    # If multiple files can be uploaded simulatenously,
    # 'file' may be a list of files.
    file = upload_receive(request)
    issue = get_object_or_404(Issue, id=issue_id)
    field = get_object_or_404(IssueField, name='file')
    event = Event.objects.create(issue=issue, field=field)
    instance = File(file=file, event=event)
    instance.save()

    basename = instance.filename()

    file_dict = {
        'name' : basename,
        'size' : file.size,

        'url': instance.file.url,
        'thumbnailUrl': instance.file.url,

        'deleteUrl': reverse('jfu_delete', kwargs = { 'pk': instance.pk }),
        'deleteType': 'POST',
    }

    return UploadResponse(request, file_dict)

@require_POST
def upload_delete(request, pk):
    success = True
    try:
        instance = File.objects.get(pk = pk)
        os.unlink(instance.file.path)
        instance.delete()
    except File.DoesNotExist:
        success = False

    return JFUResponse(request, success)
