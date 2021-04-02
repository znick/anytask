# coding: utf-8

import os
import uuid
from decimal import Decimal

from anyrb.common import AnyRB
from anyrb.common import update_status_review_request
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from issues.model_issue_field import IssueField
from issues.model_issue_status import IssueStatus
from tasks.models import Task
from unidecode import unidecode
from users.common import get_user_fullname, get_user_link


def get_file_path(instance, filename):
    return '/'.join(['files', str(uuid.uuid4()), filename])


def normalize_decimal(number):
    new_number = Decimal(str(number))
    new_number = new_number.normalize()
    exponent = new_number.as_tuple()[2]
    if exponent > 10:
        new_number = Decimal(0)
    elif exponent > 0:
        new_number = new_number.quantize(1)

    return new_number


class File(models.Model):
    file = models.FileField(upload_to=get_file_path, null=True, blank=True, max_length=500)
    event = models.ForeignKey('Event')
    deleted = models.BooleanField(default=False)

    def filename(self):
        return os.path.basename(self.file.name)


class Issue(models.Model):
    student = models.ForeignKey(User, db_index=True, null=False, blank=False, related_name='student')
    task = models.ForeignKey(Task, db_index=True, null=True, blank=False)

    mark = models.FloatField(db_index=False, null=False, blank=False, default=0)

    create_time = models.DateTimeField(auto_now_add=True)  # remove default=timezone.now
    update_time = models.DateTimeField(default=timezone.now)

    responsible = models.ForeignKey(User, db_index=True, null=True, blank=True, related_name='responsible')
    followers = models.ManyToManyField(User, blank=True)

    STATUS_NEW = 'new'
    STATUS_AUTO_VERIFICATION = 'auto_verification'
    STATUS_NEED_INFO = 'need_info'
    HIDDEN_STATUSES = {STATUS_NEW: 1,
                       STATUS_AUTO_VERIFICATION: 2,
                       STATUS_NEED_INFO: 6}

    STATUS_REWORK = IssueStatus.STATUS_REWORK
    STATUS_VERIFICATION = IssueStatus.STATUS_VERIFICATION
    STATUS_ACCEPTED = IssueStatus.STATUS_ACCEPTED

    ISSUE_STATUSES = (
        (STATUS_NEW, _(u'novyj')),
        (STATUS_REWORK, _(u'na_dorabotke')),
        (STATUS_VERIFICATION, _(u'na_proverke')),
        (STATUS_ACCEPTED, _(u'zachteno')),
        (STATUS_AUTO_VERIFICATION, _(u'na_avtomaticheskoj_proverke')),
        (STATUS_NEED_INFO, _(u'trebuetsja_informacija')),
    )

    status = models.CharField(max_length=20, choices=ISSUE_STATUSES, default=STATUS_NEW)
    status_field = models.ForeignKey(IssueStatus, db_index=True, null=False, blank=False, default=1)

    def is_status_accepted(self):
        return self.status_field.tag in [IssueStatus.STATUS_ACCEPTED, IssueStatus.STATUS_ACCEPTED_AFTER_DEADLINE]

    def is_status_only_accepted(self):
        return self.status_field.tag == IssueStatus.STATUS_ACCEPTED

    def is_status_accepted_after_deadline(self):
        return self.status_field.tag == IssueStatus.STATUS_ACCEPTED_AFTER_DEADLINE

    def is_status_auto_verification(self):
        return self.status_field.tag == IssueStatus.STATUS_AUTO_VERIFICATION

    def is_status_new(self):
        return self.status_field.tag == IssueStatus.STATUS_NEW

    def is_status_rework(self):
        return self.status_field.tag == IssueStatus.STATUS_REWORK

    def is_status_need_info(self):
        return self.status_field.tag == IssueStatus.STATUS_NEED_INFO

    def is_status_verification(self):
        return self.status_field.tag == IssueStatus.STATUS_VERIFICATION

    def score(self):
        field = IssueField.objects.get(id=8)

        mark = self.get_field_value(field)
        if mark:
            mark = normalize_decimal(mark)
        else:
            mark = 0
        return mark

    def last_comment(self):
        field = IssueField.objects.get(id=1)
        comment = self.get_field_value(field)
        if not comment:
            comment = ''

        return comment

    def get_field_repr(self, field, lang=settings.LANGUAGE_CODE):
        name = field.name

        if name == 'student_name':
            return get_user_link(self.student)
        if name == 'responsible_name':
            if self.responsible:
                return get_user_link(self.responsible)
            return None
        if name == 'followers_names':
            followers = map(
                lambda x: u'<a class="user" href="{0}">{1}</a>'.format(
                    x.get_absolute_url(), get_user_fullname(x)
                ),
                self.followers.all()
            )
            return ', '.join(followers)
        if name == 'course_name':
            course = self.task.course
            return u'<a href="{0}">{1}</a>'.format(course.get_absolute_url(), course.name)
        if name == 'task_name':
            task = self.task
            return task.get_title(lang)
        if name == 'comment':
            return None
        if name == 'status':
            return self.status_field.get_name(lang)
        if name == 'mark':
            return self.score()
        if name == 'review_id' and self.task.rb_integrated:
            return u'<a href="{1}/r/{0}">{0}</a>'.format(
                self.get_byname('review_id'),
                settings.RB_API_URL,
            )
        if name == 'run_id' and self.task.contest_integrated:
            return u'<a href="https://contest.yandex.ru/contest/{1}/run-report/{0}">{0}</a>'.format(
                self.get_byname('run_id'),
                self.task.contest_id,
            )

        return self.get_field_value(field)

    def get_byname(self, name):
        field = IssueField.objects.get(name=name)
        return self.get_field_value(field)

    def get_field_value(self, field):
        name = field.name
        if name == 'student_name':
            return self.student
        if name == 'responsible_name':
            if self.responsible:
                return self.responsible
            return None
        if name == 'followers_names':
            ret = []
            for user in self.followers.all():
                ret.append(user.id)
            return ret
        if name == 'course_name':
            return self.task.course
        if name == 'task_name':
            return self.task
        if name == 'status':
            return self.status_field
        if name == 'max_mark':
            return self.task.score_max
        if name == 'mark':
            return self.mark

        events = Event.objects.filter(issue_id=self.id, field_id=field.id).order_by('-timestamp')[:1]
        if not events:
            fields_count = self.task.course.issue_fields.filter(id=field.id).count()
            if fields_count:
                self.set_field(field, field.get_default_value())
                if field.get_default_value() is not None:
                    return field.get_default_value()
                return ''
            else:
                raise AttributeError('field_name = {0}'.format(name))

        return events[0].value

    def get_field_value_for_form(self, field):
        ret = self.get_field_value(field)
        if field.name == 'responsible_name':
            if ret:
                ret = ret.id  # Hack hack hack :\
            return ret
        if field.name == 'status':
            if ret.id not in IssueStatus.HIDDEN_STATUSES.values():
                ret = ret.id
            else:
                ret = None
            return ret
        return ret

    def create_event(self, field, author):
        event = Event()
        event.issue = self
        event.field = field
        event.author = author
        event.save()

        return event

    def set_status_by_id(self, status_id, author=None):
        if int(status_id) in IssueStatus.HIDDEN_STATUSES.values():
            return self.set_byname('status', IssueStatus.objects.get(id=status_id))
        else:
            status = self.task.course.issue_status_system.statuses.filter(id=status_id)
            if status:
                return self.set_byname('status', status[0], author)

    def set_status_by_tag(self, tag, author=None):
        if tag in IssueStatus.HIDDEN_STATUSES:
            return self.set_byname('status', IssueStatus.objects.get(id=IssueStatus.HIDDEN_STATUSES[tag]))
        else:
            status = self.task.course.issue_status_system.statuses.filter(tag=tag)
            if status:
                return self.set_byname('status', status[0], author)
        return

    def set_status_accepted(self, author=None):
        self.set_status_by_tag(IssueStatus.STATUS_ACCEPTED, author)

    def set_status_new(self, author=None):
        self.set_status_by_tag(IssueStatus.STATUS_NEW, author)

    def set_status_accepted_after_deadline(self, author=None):
        self.set_status_by_tag(IssueStatus.STATUS_ACCEPTED_AFTER_DEADLINE, author)

    def set_status_need_info(self, author=None):
        self.set_status_by_tag(IssueStatus.STATUS_NEED_INFO, author)

    def set_status_rework(self, author=None):
        self.set_status_by_tag(IssueStatus.STATUS_REWORK, author)

    def set_status_auto_verification(self, author=None):
        self.set_status_by_tag(IssueStatus.STATUS_AUTO_VERIFICATION, author)

    def set_status_verification(self, author=None):
        self.set_status_by_tag(IssueStatus.STATUS_VERIFICATION, author)

    def set_status_seminar(self, author=None):
        self.set_status_by_tag(IssueStatus.STATUS_SEMINAR, author)

    def set_byname(self, name, value, author=None, from_contest=False):
        field = IssueField.objects.get(name=name)
        return self.set_field(field, value, author, from_contest)

    def set_field(self, field, value, author=None, from_contest=False):
        event = self.create_event(field, author)
        name = field.name
        course = self.task.course

        delete_event = False

        if name == 'responsible_name':
            new_responsible = value

            if self.responsible != new_responsible:
                new_followers = list(self.followers.all().exclude(id=new_responsible.id))
                if self.responsible:
                    new_followers.append(self.responsible)
                self.responsible = new_responsible
                self.followers = new_followers
            else:
                delete_event = True

            value = get_user_fullname(value)

        elif name == 'followers_names':
            if self.responsible and str(self.responsible.id) in value:
                value.remove(str(self.responsible.id))
            new_followers = User.objects.filter(id__in=value)

            if list(new_followers) == list(self.followers.all()):
                delete_event = True
            else:
                deleted_followers = [get_user_fullname(follower)
                                     for follower in set(self.followers.all()).difference(set(new_followers))]
                add_followers = [get_user_fullname(follower) for follower in new_followers.all()]
                self.followers = value
                value = ', '.join(add_followers) + '\n' + ', '.join(deleted_followers)

        elif name == 'comment':
            if value:
                sent = True
                for file_id, file in enumerate(value['files']):
                    file.name = unidecode(file.name)
                    uploaded_file = File(file=file, event=event)
                    uploaded_file.save()
                    if self.task.contest_integrated:
                        for ext in settings.CONTEST_EXTENSIONS:
                            filename, extension = os.path.splitext(file.name)
                            if ext == extension:
                                contest_submission = self.contestsubmission_set.create(
                                    issue=self, author=author, file=uploaded_file
                                )
                                sent = contest_submission.upload_contest(ext, compiler_id=value['compilers'][file_id])
                                if sent:
                                    value['comment'] += u"<p>{0}</p>".format(_(u'otpravleno_v_kontest'))
                                    if not self.is_status_accepted():
                                        self.set_status_auto_verification()
                                else:
                                    value['comment'] += u"<p>{0}('{1}')</p>".format(_(u'oshibka_otpravki_v_kontest'),
                                                                                    contest_submission.send_error)
                                    self.followers.add(User.objects.get(username='anytask.monitoring'))
                                break

                    if self.task.rb_integrated \
                            and (course.send_rb_and_contest_together or not self.task.contest_integrated):
                        for ext in settings.RB_EXTENSIONS + [str(ext.name) for ext in course.filename_extensions.all()]:
                            filename, extension = os.path.splitext(file.name)
                            if ext == extension or ext == '.*':
                                anyrb = AnyRB(event)
                                review_request_id = anyrb.upload_review()
                                if review_request_id is not None:
                                    value['comment'] += u'<p><a href="{1}/r/{0}">Review request {0}</a></p>'. \
                                        format(review_request_id, settings.RB_API_URL)
                                else:
                                    value['comment'] += u'<p>{0}</p>'.format(_(u'oshibka_otpravki_v_rb'))
                                    self.followers.add(User.objects.get(username='anytask.monitoring'))
                                break

                if not value['files'] and not value['comment']:
                    event.delete()
                    return
                else:
                    self.update_time = timezone.now()
                    value = u'<div class="issue-page-comment not-sanitize">' + value['comment'] + u'</div>'

                if not self.is_status_auto_verification() and not self.is_status_accepted():
                    if author == self.student and not self.is_status_need_info() and sent:
                        self.set_status_verification()
                    if author == self.responsible:
                        if self.is_status_need_info():
                            status_field = IssueField.objects.get(name='status')
                            status_events = Event.objects \
                                .filter(issue_id=self.id, field=status_field) \
                                .exclude(author__isnull=True) \
                                .order_by('-timestamp')

                            if status_events:
                                status_prev = self.task.course.issue_status_system.statuses \
                                    .filter(name=status_events[0].value)
                                if status_prev:
                                    self.set_field(status_field, status_prev[0])
                                else:
                                    self.set_status_rework()
                        else:
                            self.set_status_rework()

        elif name == 'status':
            try:
                review_id = self.get_byname('review_id')
                if review_id != '':
                    if value.tag in [IssueStatus.STATUS_ACCEPTED, IssueStatus.STATUS_ACCEPTED_AFTER_DEADLINE]:
                        update_status_review_request(review_id, 'submitted')
                    elif self.is_status_accepted():
                        update_status_review_request(review_id, 'pending')
            except:  # noqa
                pass

            if self.status_field != value:
                if self.task.parent_task is not None:
                    parent_task_issue, created = Issue.objects.get_or_create(
                        student=self.student,
                        task=self.task.parent_task
                    )
                    if not self.task.score_after_deadline:
                        if self.is_status_accepted_after_deadline():
                            parent_task_issue.mark += self.mark
                        elif value.tag == IssueStatus.STATUS_ACCEPTED_AFTER_DEADLINE:
                            parent_task_issue.mark -= self.mark
                    parent_task_issue.set_status_seminar()
                self.status_field = value
            else:
                delete_event = True

            value = self.status_field.get_name()

        elif name == 'mark':
            if not value:
                value = 0
            value = min(normalize_decimal(value), self.task.score_max)
            if self.mark != float(value):
                if self.task.parent_task and \
                        (self.task.score_after_deadline
                         or not (not self.task.score_after_deadline and self.is_status_accepted_after_deadline())):
                    parent_task_issue, created = Issue.objects.get_or_create(
                        student=self.student,
                        task=self.task.parent_task
                    )
                    parent_task_issue.mark += float(value) - self.mark
                    parent_task_issue.set_status_seminar()

                self.mark = float(value)
            else:
                delete_event = True

            value = str(value)
            if not from_contest and not self.is_status_accepted() and not self.is_status_new():
                self.set_status_rework()

        self.save()

        if not value:
            value = ''

        if not delete_event:
            event.value = value
            event.save()
            event.pull_plugins()
        else:
            event.delete()

        return

    def set_teacher(self, groups=None, teacher=None, default=False, author=None):
        if default:
            for group in groups if groups else self.task.groups.filter(students=self.student):
                default_teacher = self.task.course.get_default_teacher(group)
                if default_teacher and (not self.get_byname('responsible_name')):
                    self.set_byname('responsible_name', default_teacher, author)
        else:
            self.set_byname('responsible_name', teacher, author)

    def get_history(self):
        """
        :returns event objects
        """
        events = Event.objects.filter(issue_id=self.id).exclude(Q(author__isnull=True)
                                                                | Q(field__name='review_id')).order_by('timestamp')
        return events

    def __unicode__(self):
        return u'Issue: {0} {1}'.format(self.id, self.task.get_title())

    def get_absolute_url(self):
        return reverse('issues.views.issue_page', args=[str(self.id)])

    def add_comment(self, comment, author=None):
        if author is None:
            author = User.objects.get(username="anytask")
        field, field_get = IssueField.objects.get_or_create(name='comment')
        event = self.create_event(field, author=author)
        event.value = u'<div class="contest-response-comment not-sanitize">' + comment + u'</div>'
        event.save()
        return event

    class Meta:
        unique_together = ("student", "task")


class Event(models.Model):
    issue = models.ForeignKey(Issue, null=False, blank=False)
    author = models.ForeignKey(User, db_index=True, null=True, blank=True)
    field = models.ForeignKey(IssueField, blank=False, default=1)

    value = models.TextField(max_length=2500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    sended_notify = models.BooleanField(default=False)

    def pull_plugins(self):
        # upload_review(self)
        # from anycontest.common import AnyContest
        # AnyContest(self)
        pass

    def get_message(self):
        msg_map = {
            'responsible_name': _('zadachu_proveriaet'),
            'status': _('status_izmenen'),
            'mark': _('ocenka_izmenena'),
            'file': _('zagruzhen_faij')
        }
        message = ''
        if self.field.name == 'followers_names':
            value = self.value.split('\n')
            if len(value) == 1:
                return _('nabludaiut') + ' ' + self.value if self.value else _('nabludaet_nikto')
            new_users, deleted_users = value
            if new_users:
                message += u'{0} {1}'.format(_('nabludaiut'), new_users)
            if deleted_users:
                message += u'\n{0} {1}'.format(_('ne_nabludaiut'), deleted_users)
        else:
            if self.field.history_message:
                if self.field.name in msg_map:
                    message += msg_map[self.field.name] + ' '
                else:
                    message += self.field.history_message + ' '
            message += self.value
        return message

    def get_notify_message(self):
        message = list()
        timestamp = self.timestamp.strftime('%d %b %H:%M')
        message.append(timestamp.decode('utf-8'))
        message.append(u'{0}:'.format(get_user_fullname(self.author)))
        message.append(self.get_message())
        if self.file_set.all():
            file_list = list()
            for file in self.file_set.all():
                file_list.append(file.filename())
            message.append(', '.join(file_list))
        return u'\n'.join(message)

    def is_comment(self):
        return self.field.name == 'comment'

    def is_change(self):
        return self.field.name != 'comment'

    #    def save(self, *a, **ka):
    #        import traceback
    #        traceback.print_stack()
    #        return super(self.__class__, self).save(*a, **ka)

    def __unicode__(self):
        if not self.author:
            ret = u'{0} nobody'.format(self.issue.id)
        else:
            ret = u'{1} {0}'.format(self.author.first_name,
                                    self.issue.id)
        if self.is_change():
            ret += u' {0}'.format(self.field.name)
        return ret


@receiver(models.signals.post_save, sender=Issue)
def post_create_set_default_teacher(sender, instance, created, *args, **kwargs):
    if created:
        instance.set_teacher(default=True)
