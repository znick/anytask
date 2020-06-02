# -*- coding: utf-8 -*-
import os
from copy import deepcopy

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from jfu.http import upload_receive, UploadResponse, JFUResponse
from unidecode import unidecode
from django.db.transaction import atomic

from anycontest.common import get_problem_compilers
from anyrb.common import AnyRB
from issues.model_issue_field import IssueField
from issues.model_issue_status import IssueStatus
from issues.models import Issue, Event, File


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
    title_map = {'comment': _('kommentarij'),
                 'course_name': _('kurs'),
                 'task_name': _('zadacha'),
                 'student_name': _('student'),
                 'responsible_name': _('proverjaushij'),
                 'followers_names': _('nabludateli'),
                 'status': _('status'),
                 'mark': _('ocenka'),
                 'file': _('fajl'),
                 'review_id': _('nomer_revju'),
                 'run_id': _('nomer_posylki_kontest')
                 }

    user = request.user
    lang = user.profile.language
    for field in info_fields:
        field.editable = field.can_edit(user, issue)
        if field.is_visible():
            field.repr = issue.get_field_repr(field, lang)

        field.value = issue.get_field_value_for_form(field)

        data = {field.name: field.value}
        field.form = field.get_form(request, issue, data)
        field.title = title_map[field.name] if field.name in title_map else field.title


def contest_rejudge(issue):
    got_verdict_submissions = issue.contestsubmission_set.filter(got_verdict=True)

    if not (got_verdict_submissions.count()
            and issue.contestsubmission_set.count()
            == (
                got_verdict_submissions.count()
                + issue.contestsubmission_set.exclude(send_error__isnull=True).exclude(send_error="").count())
            ):
        return

    old_contest_submission = got_verdict_submissions.order_by("-create_time")[0]
    author = old_contest_submission.author
    field, field_get = IssueField.objects.get_or_create(name='comment')
    event = issue.create_event(field, author=author)

    file_copy = deepcopy(old_contest_submission.file)
    file_copy.pk = None
    file_copy.event = event
    file_copy.save()
    contest_submission = issue.contestsubmission_set.create(issue=issue,
                                                            author=author,
                                                            file=file_copy)
    sent = contest_submission.upload_contest(compiler_id=old_contest_submission.compiler_id)
    if sent:
        event.value = u"<p>{0}</p>".format(_(u'otpravleno_v_kontest'))
        if not issue.is_status_accepted():
            issue.set_status_auto_verification()
    else:
        event.value = u"<p>{1}('{0}').</p>".format(
            contest_submission.send_error, _(u'oshibka_otpravki_v_kontest'))
        issue.followers.add(User.objects.get(username='anytask.monitoring'))

    if issue.task.rb_integrated and issue.task.course.send_rb_and_contest_together:
        for ext in settings.RB_EXTENSIONS + [str(ext.name) for ext in issue.task.course.filename_extensions.all()]:
            filename, extension = os.path.splitext(file_copy.file.name)
            if ext == extension or ext == '.*':
                anyrb = AnyRB(event)
                review_request_id = anyrb.upload_review()
                if review_request_id is not None:
                    event.value += u'<p><a href="{1}/r/{0}">Review request {0}</a></p>'. \
                        format(review_request_id, settings.RB_API_URL)
                else:
                    event.value += u'<p>{0}.</p>'.format(_(u'oshibka_otpravki_v_rb'))
                    issue.followers.add(User.objects.get(username='anytask.monitoring'))
                break

    event.save()


@login_required
def issue_page(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)
    user = request.user
    if not user_can_read(user, issue):
        raise PermissionDenied

    issue_fields = issue.task.course.issue_fields.all()

    seminar = issue.task.parent_task

    if request.method == 'POST':
        if 'contest_rejudge' in request.POST:
            contest_rejudge(issue)
            return HttpResponseRedirect('')

        form_name = request.POST['form_name']

        for field in issue_fields:
            if form_name == u'{0}_form'.format(field.name):
                form = field.get_form(request, issue)

                if form.is_valid():
                    value = form.cleaned_data[field.name]

                    if field.name in ['mark', 'status', 'responsible_name', 'followers_names']:
                        if not user_is_teacher_or_staff(request.user, issue):
                            raise PermissionDenied

                    if 'Me' in request.POST:
                        if field.name == 'responsible_name':
                            value = request.user
                        else:
                            if request.user not in value:
                                value.append(str(request.user.id))
                    if 'Accepted' in request.POST:
                        if request.POST['Accepted']:
                            issue.set_byname('status',
                                             IssueStatus.objects.get(pk=request.POST['Accepted']),
                                             request.user)
                        else:
                            issue.set_status_accepted(request.user)

                    if field.name == 'comment':
                        value = {
                            'comment': value,
                            'files': request.FILES.getlist('files')
                        }
                        if 'need_info' in request.POST and any(value.itervalues()):
                            issue.set_status_need_info()

                    issue.set_field(field, value, request.user)

                    if 'comment_verdict' in request.POST:
                        issue.set_byname('comment',
                                         {'files': [], 'comment': request.POST['comment_verdict']},
                                         request.user)

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

    lang = user.profile.language
    statuses_accepted = [(status.id, status.get_name(lang))
                         for status in issue.task.course.issue_status_system.get_accepted_statuses()]

    schools = issue.task.course.school_set.all()

    show_contest_rejudge_loading = False
    if issue.contestsubmission_set \
            .exclude(run_id__exact="") \
            .exclude(run_id__isnull=True) \
            .filter(send_error__isnull=True, got_verdict=False) \
            .count():
        show_contest_rejudge_loading = True

    show_contest_rejudge = False
    got_verdict_submissions = issue.contestsubmission_set.filter(got_verdict=True)
    if got_verdict_submissions.count() and not show_contest_rejudge_loading:
        show_contest_rejudge = True

    if seminar:
        seminar_url = issue.task.course.get_absolute_url() + "/seminar/" + str(seminar.id)
    else:
        seminar_url = None

    context = {
        'issue': issue,
        'issue_fields': issue_fields,
        'course': issue.task.course,
        'seminar_url': seminar_url,
        'events_to_show': events_to_show,
        'first_event_after_deadline': first_event_after_deadline,
        'show_top_alert': show_top_alert,
        'teacher_or_staff': user_is_teacher_or_staff(request.user, issue),
        'school': schools[0] if schools else '',
        'visible_queue': issue.task.course.user_can_see_queue(request.user),
        'statuses_accepted': statuses_accepted,
        'show_contest_rejudge': show_contest_rejudge,
        'show_contest_rejudge_loading': show_contest_rejudge_loading,
        'show_contest_run_id': issue.task.course.user_can_see_contest_run_id(request.user),
        'jupyterhub_url': getattr(settings, 'JUPYTERHUB_URL', ''),
        'max_file_size': getattr(settings, 'MAX_FILE_SIZE', 1024 * 1024 * 100),
        'max_files_number': getattr(settings, 'MAX_FILES_NUMBER', 10)
    }

    return render(request, 'issues/issue.html', context)


@login_required
@atomic
def get_or_create(request, task_id, student_id):
    # if not request.is_ajax():
    #    return HttpResponseForbidden()

    issue, created = Issue.objects.get_or_create(task_id=task_id, student_id=student_id)

    # data = {
    #     'issue_url': issue.get_absolute_url(),
    # }

    return HttpResponsePermanentRedirect(
        "/issue/" + str(issue.id))  # (json.dumps(data), content_type='application/json')


@login_required
@require_POST
def upload(request):
    # The assumption here is that jQuery File Upload
    # has been configured to send files one at a time.
    # If multiple files can be uploaded simulatenously,
    # 'file' may be a list of files.
    issue = get_object_or_404(Issue, id=int(request.POST['issue_id']))

    if 'update_issue' in request.POST:
        event_value = {'files': [], 'comment': '', 'compilers': []}
        event_value['comment'] = request.POST['comment']
        file_counter = 0
        for field, value in dict(request.POST).items():
            if 'compiler' in field:
                pk = int(field[13:])
                file = File.objects.get(pk=pk)
                compiler_id = value
                event_value['files'].append(file.file)
                event_value['compilers'].append(compiler_id)

            if 'pk' in field:
                pk = int(value[0])
                file = File.objects.get(pk=pk)
                file_counter += 1
                event_value['files'].append(file.file)
                event_value['compilers'].append(None)

        if not (issue.task.one_file_upload and file_counter > 1):
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

    one_file_upload = False
    if issue.task.one_file_upload:
        filename, extension = os.path.splitext(file.name)
        file.name = 'upload' + extension
        one_file_upload = True
    else:
        file.name = unidecode(file.name)

    instance = File(file=file, event=event)
    instance.save()

    basename = instance.filename()

    file_dict = {
        'name': basename,
        'size': file.size,

        'url': instance.file.url,
        'thumbnailUrl': instance.file.url,

        'delete_url': reverse('jfu_delete', kwargs={'pk': instance.pk}),
        'delete_type': 'POST',

        'problem_compilers': problem_compilers,
        'chosen_compiler': chosen_compiler,
        'pk': instance.pk,
        'send_to_contest': send_to_contest,

        'one_file_upload': one_file_upload,
    }

    return UploadResponse(request, file_dict)


@login_required
@require_POST
def upload_delete(request, pk):
    success = True
    try:
        instance = File.objects.get(pk=pk)
        os.unlink(instance.file.path)
        instance.delete()
    except File.DoesNotExist:
        success = False

    return JFUResponse(request, success)
