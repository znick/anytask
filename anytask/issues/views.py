# -*- coding: utf-8 -*-
import pprint
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
import json
import os   
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.context import RequestContext
from issues.forms import FileForm
from issues.models import Issue, Event, File
from issues.model_issue_field import IssueField

from django.core.urlresolvers import reverse
from django.views import generic
from django.views.decorators.http import require_POST
from jfu.http import upload_receive, UploadResponse, JFUResponse

from anycontest.common import get_problem_compilers

from unidecode import unidecode

def user_is_teacher_or_staff(user, issue):
    if user.is_staff:
        return True
    if issue.task.course.user_is_teacher(user):
        return True
    return False


def user_can_read(user, issue):
    if not issue.task.has_issue_access():
        return False
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

    first_event_after_deadline = None
    events_to_show = 6
    show_top_alert = False

    for event_id, event in enumerate(issue.get_history()):
        if issue.task.deadline_time and event.timestamp > issue.task.deadline_time:
            first_event_after_deadline = event
            if event_id < len(issue.get_history()) - events_to_show:
                show_top_alert = True
            break

    schools = issue.task.course.school_set.all()

    context = {
        'issue': issue,
        'issue_fields': issue_fields,
        'course': issue.task.course,
        'events_to_show': events_to_show,
        'first_event_after_deadline': first_event_after_deadline,
        'show_top_alert': show_top_alert,
        'teacher_or_staff': user_is_teacher_or_staff(request.user, issue),
        'school': schools[0] if schools else '',
        'visible_queue': issue.task.course.user_can_see_queue(request.user),
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
def upload(request):

    # The assumption here is that jQuery File Upload
    # has been configured to send files one at a time.
    # If multiple files can be uploaded simulatenously,
    # 'file' may be a list of files.
    issue = get_object_or_404(Issue, id=int(request.POST['issue_id']))

    if 'update_issue' in request.POST:
        event_value = {'files':[], 'comment':'', 'compilers':[]}
        event_value['comment'] = request.POST['comment']
        for field, value in dict(request.POST).iteritems():
            if 'compiler' in field:
                pk = int(field[13:])
                file = File.objects.get(pk = pk)
                compiler_id = value
                event_value['files'].append(file.file)
                event_value['compilers'].append(compiler_id)

            if 'pk' in field:
                pk = int(value[0])
                file = File.objects.get(pk = pk)
                event_value['files'].append(file.file)
                event_value['compilers'].append(None)

        issue.set_byname('comment', event_value, request.user)

        return redirect(issue_page, issue_id=int(request.POST['issue_id']))

    file = upload_receive(request)
    field = get_object_or_404(IssueField, name='file')
    event = Event.objects.create(issue_id=issue.id, field=field)

    problem_compilers = []
    chosen_compiler = None
    send_to_contest = False

    if issue.task.contest_integrated:
        problem_compilers = get_problem_compilers(issue.task.problem_id, issue.task.contest_id)
        for ext in settings.CONTEST_EXTENSIONS:
            filename, extension = os.path.splitext(file.name)
            if ext == extension:
                send_to_contest = True
                if not problem_compilers:
                    chosen_compiler = settings.CONTEST_EXTENSIONS[ext]
                if settings.CONTEST_EXTENSIONS[ext] in problem_compilers:
                    chosen_compiler = settings.CONTEST_EXTENSIONS[ext]
                    problem_compilers.remove(chosen_compiler)

    file.name = unidecode(file.name)
    instance = File(file=file, event=event)
    instance.save()

    basename = instance.filename()

    file_dict = {
        'name' : basename,
        'size' : file.size,

        'url': instance.file.url,
        'thumbnailUrl': instance.file.url,

        'delete_url': reverse('jfu_delete', kwargs = { 'pk': instance.pk }),
        'delete_type': 'POST',

        'problem_compilers': problem_compilers,
        'chosen_compiler' : chosen_compiler,
        'pk': instance.pk,
        'send_to_contest': send_to_contest,
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
