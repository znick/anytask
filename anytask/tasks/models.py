# coding: utf-8

import copy
import sys
import json
from datetime import timedelta
from django.utils import timezone

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Max
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.utils.html import escape

from courses.models import Course
from groups.models import Group


def check_json(text):
    try:
        text_to_json = json.loads(text, strict=False)
        if not isinstance(text_to_json, dict):
            raise ValueError
        return text_to_json
    except (ValueError, TypeError):
        return False


def get_lang_text(text, lang):
    text_ = check_json(text)
    if text_:
        lang = lang if lang in text_ else settings.LANGUAGE_CODE
        return text_[lang]
    return unicode(text)


class Task(models.Model):
    title = models.CharField(max_length=191, db_index=True, null=True, blank=True)
    short_title = models.CharField(max_length=15, db_index=True, null=True, blank=True)
    course = models.ForeignKey(Course, db_index=True, null=False, blank=False)
    group = models.ForeignKey(Group, db_index=False, null=True, blank=True, default=None)
    groups = models.ManyToManyField(Group, blank=False, related_name='groups_set')

    weight = models.IntegerField(db_index=True, null=False, blank=False, default=0)

    is_hidden = models.BooleanField(db_index=True, null=False, blank=False, default=False)

    parent_task = models.ForeignKey('self', db_index=True, null=True, blank=True, related_name='children')

    task_text = models.TextField(null=True, blank=True, default=None)

    score_max = models.IntegerField(db_index=True, null=False, blank=False, default=0)

    max_students = models.IntegerField(null=False, blank=False, default=0)

    contest_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    rb_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    TYPE_FULL = 'All'
    TYPE_SIMPLE = 'Only mark'
    TYPE_SEMINAR = 'Seminar'
    TYPE_MATERIAL = 'Material'
    TYPE_IPYNB = 'Jupyter Notebook'
    TASK_TYPE_CHOICES = (
        (TYPE_FULL, _('s_obsuzhdeniem')),
        (TYPE_SIMPLE, _('tolko_ocenka')),
        (TYPE_MATERIAL, _('material')),
        (TYPE_SEMINAR, _('seminar')),
        (TYPE_IPYNB, _('jupyter notebook'))
    )
    type = models.CharField(db_index=False, max_length=128, choices=TASK_TYPE_CHOICES, default=TYPE_FULL)

    added_time = models.DateTimeField(auto_now_add=True)  # remove default=timezone.now
    update_time = models.DateTimeField(auto_now=True)  # remove default=timezone.now
    deadline_time = models.DateTimeField(auto_now=False, blank=True, null=True, default=None)

    updated_by = models.ForeignKey(User, db_index=False, null=True, blank=True)

    contest_id = models.IntegerField(db_index=True, null=False, blank=False, default=0)
    problem_id = models.CharField(max_length=128, db_index=True, null=True, blank=True)

    send_to_users = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    sended_notify = models.BooleanField(db_index=True, null=False, blank=False, default=True)

    one_file_upload = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    accepted_after_contest_ok = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    score_after_deadline = models.BooleanField(db_index=False, null=False, blank=False, default=True)

    nb_assignment_name = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.title)

    def get_title(self, lang=settings.LANGUAGE_CODE):
        return escape(get_lang_text(self.title, lang))

    def get_description(self, lang=settings.LANGUAGE_CODE):
        return get_lang_text(self.task_text, lang)

    def is_text_json(self):
        return check_json(self.task_text)

    @property
    def max_students_on_task(self):
        return self.max_students or self.course.max_students_per_task or settings.PYTHONTASK_MAX_USERS_PER_TASK

    def user_can_take_task(self, user):
        for task_taken in TaskTaken.objects.filter(task=self):
            task_taken.update_status()

        if user.is_anonymous():
            return (False, 'Необходимо залогиниться')

        if self.is_hidden:
            return (False, 'Задача скрыта')

        if not self.course.groups.filter(students=user).count():
            return (False, u'Необходимо числиться в одной из групп курса')

        if Task.objects.filter(parent_task=self).count() > 0:
            return (False, u'')

        if TaskTaken.objects.filter(task=self).filter(user=user).filter(
                Q(Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED))).count() != 0:
            return (False, u'')

        if self.parent_task is not None:
            tasks = Task.objects.filter(parent_task=self.parent_task)
            if TaskTaken.objects.filter(user=user).filter(task__in=tasks) \
                    .exclude(status=TaskTaken.STATUS_CANCELLED) \
                    .exclude(status=TaskTaken.STATUS_DELETED) \
                    .count() > 0:
                return (False, u'Вы уже взяли другую подзадачу из этой задачи')

        max_not_scored_tasks = self.course.max_not_scored_tasks or \
            settings.PYTHONTASK_MAX_TASKS_WITHOUT_SCORE_PER_STUDENT
        if max_not_scored_tasks:
            if TaskTaken.objects.filter(user=user) \
                                .filter(task__course=self.course) \
                                .filter(status=TaskTaken.STATUS_TAKEN).count() >= max_not_scored_tasks:
                return (False, u'У вас слишком много неоцененных задач')

        max_incomplete_tasks = self.course.max_incomplete_tasks or settings.PYTHONTASK_MAX_INCOMPLETE_TASKS
        if max_incomplete_tasks:
            all_scored = TaskTaken.objects.filter(user=user).filter(task__course=self.course) \
                                                            .filter(Q(Q(status=TaskTaken.STATUS_TAKEN) | Q(
                                                                status=TaskTaken.STATUS_SCORED)))
            if sum(t.score != t.task.score_max for t in all_scored) + 1 > max_incomplete_tasks:
                return (False, u'У вас слишком много не до конца доделанных задач')

        max_students = self.max_students_on_task or settings.PYTHONTASK_MAX_USERS_PER_TASK
        if max_students:
            if TaskTaken.objects.filter(task=self).filter(Q(Q(status=TaskTaken.STATUS_TAKEN) | Q(
                    status=TaskTaken.STATUS_SCORED))).count() >= max_students:
                return (
                    False,
                    u'Задача не может быть взята более чем %d студентами' % max_students)

        try:
            task_taken = TaskTaken.objects.filter(task=self).filter(user=user).get(status=TaskTaken.STATUS_BLACKLISTED)
            blacklist_expired_date = task_taken.blacklisted_till
            if blacklist_expired_date:
                return (False, u'Вы сможете взять эту задачу с %s' % blacklist_expired_date.strftime("%d.%m.%Y"))
        except TaskTaken.DoesNotExist:
            pass

        return (True, u'')

    def user_can_cancel_task(self, user):
        if user.is_anonymous() or self.is_hidden:
            return False
        if TaskTaken.objects.filter(task=self).filter(user=user).filter(status=TaskTaken.STATUS_TAKEN).count() != 0:
            return True
        return False

    def user_can_score_task(self, user):
        if user.is_anonymous():
            return False

        return self.course.user_is_teacher(user)

    def user_can_pass_task(self, user):
        if user.is_anonymous():
            return False

        if not self.course.is_python_task:
            if self.user_can_take_task(user):
                return True

        try:
            task_taken = self.get_task_takens().get(user=user)
            return (task_taken.status == TaskTaken.STATUS_TAKEN or task_taken.status == TaskTaken.STATUS_SCORED)
        except TaskTaken.DoesNotExist:
            return False
        return False

    def has_parent(self):
        return self.parent_task is not None

    def has_subtasks(self):
        return Task.objects.filter(parent_task=self).count() > 0

    def get_subtasks(self):
        return Task.objects.filter(parent_task=self)

    def get_task_takens(self):
        return TaskTaken.objects.filter(task=self).filter(
            Q(Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED)))

    def add_user_properties(self, user):
        self.can_take = self.user_can_take_task(user)
        self.can_cancel = self.user_can_cancel_task(user)
        self.can_score = self.user_can_score_task(user)
        self.can_pass = self.user_can_pass_task(user)
        self.is_shown = not self.is_hidden or self.course.user_is_teacher(user)

    def has_issue_access(self):
        return self.type not in [self.TYPE_SIMPLE, self.TYPE_MATERIAL, self.TYPE_SEMINAR]

    def set_position_in_new_group(self, groups=None):
        if not groups:
            groups = self.course.groups.all()
        else:
            for task_related in TaskGroupRelations.objects.filter(task=self).exclude(group__in=groups):
                task_related.deleted = True
                task_related.save()

        for group in list(groups):
            task_related, created = TaskGroupRelations.objects.get_or_create(task=self, group=group)

            if created:
                max_position = TaskGroupRelations.objects.filter(group=group).exclude(id=task_related.id) \
                    .aggregate(Max('position'))['position__max']
                task_related.position = max_position + 1 if max_position is not None else 0
            else:
                task_related.deleted = False
            task_related.save()

    def get_url_in_course(self):
        return reverse('courses.views.seminar_page', kwargs={'course_id': self.course_id, 'task_id': self.id})


class TaskLog(models.Model):
    title = models.CharField(max_length=191, db_index=True, null=True, blank=True)
    course = models.ForeignKey(Course, db_index=False, null=False, blank=False)
    group = models.ForeignKey(Group, db_index=False, null=True, blank=True, default=None)
    groups = models.ManyToManyField(Group, blank=False, related_name='groups_log_set')

    weight = models.IntegerField(db_index=False, null=False, blank=False, default=0)

    parent_task = models.ForeignKey('self', db_index=True, null=True, blank=True, related_name='parent_task_set')

    task_text = models.TextField(null=True, blank=True, default=None)

    score_max = models.IntegerField(db_index=False, null=False, blank=False, default=0)

    contest_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    rb_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    TYPE_FULL = 'All'
    TYPE_SIMPLE = 'Only mark'
    TASK_TYPE_CHOICES = (
        (TYPE_FULL, _(u's_obsuzhdeniem')),
        (TYPE_SIMPLE, _(u'tolko_ocenka')),
    )
    type = models.CharField(db_index=False, max_length=128, choices=TASK_TYPE_CHOICES, default=TYPE_FULL)

    added_time = models.DateTimeField(auto_now_add=True)  # remove default=timezone.now
    update_time = models.DateTimeField(auto_now=True)  # remove default=timezone.now
    deadline_time = models.DateTimeField(auto_now=False, null=True, default=None)

    updated_by = models.ForeignKey(User, db_index=False, null=True, blank=True)

    contest_id = models.IntegerField(db_index=True, null=False, blank=False, default=0)
    problem_id = models.CharField(max_length=128, db_index=True, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.title)


class TaskTaken(models.Model):
    STATUS_TAKEN = 0
    STATUS_CANCELLED = 1
    STATUS_BLACKLISTED = 2
    STATUS_SCORED = 3
    STATUS_DELETED = 4

    user = models.ForeignKey(User, db_index=True, null=False, blank=False)
    task = models.ForeignKey(Task, db_index=True, null=False, blank=False)
    issue = models.ForeignKey('issues.Issue', db_index=True, null=True, blank=False)

    TASK_TAKEN_STATUSES = (
        (STATUS_TAKEN, u'Task taken'),
        (STATUS_CANCELLED, u'Task cancelled'),
        (STATUS_BLACKLISTED, u'Task blacklisted'),
        (STATUS_SCORED, u'Task scored'),
        (STATUS_DELETED, u'TaskTaken deleted')
    )
    status = models.IntegerField(choices=TASK_TAKEN_STATUSES, db_index=True, blank=False, default=0)

    EDIT = 'EDIT'
    QUEUE = 'QUEUE'
    OK = 'OK'
    STATUS_CHECK_CHOICES = (
        (EDIT, u'Дорешивание'),
        (QUEUE, u'Ожидает проверки'),
        (OK, u'Задача зачтена и/или больше не принимается'),
    )
    status_check = models.CharField(db_index=True, max_length=5, choices=STATUS_CHECK_CHOICES, default=EDIT)

    taken_time = models.DateTimeField(blank=True, null=True)
    blacklisted_till = models.DateTimeField(blank=True, null=True)
    added_time = models.DateTimeField(auto_now_add=True)   # remove default=timezone.now
    update_time = models.DateTimeField(auto_now=True)  # remove default=timezone.now

    @property
    def score(self):
        self.update_status()
        if not self.issue:
            return 0
        return self.issue.mark

    def update_status(self):
        if self.issue and abs(self.issue.mark) > sys.float_info.epsilon and self.status != self.STATUS_SCORED:
            self.scored()

        if not self.issue.get_byname('responsible_name'):
            group = self.task.course.get_user_group(self.user)
            if group:
                default_teacher = self.task.course.get_default_teacher(group)
                if default_teacher:
                    self.issue.set_byname('responsible_name', default_teacher, author=None)

    def take(self):
        self.status = self.STATUS_TAKEN
        if self.taken_time is None:
            self.taken_time = timezone.now()
        self.save()

    def cancel(self):
        dt_from_taken_delta = timezone.now() - self.taken_time
        if (dt_from_taken_delta.days) <= settings.PYTHONTASK_MAX_DAYS_TO_FULL_CANCEL:
            self.taken_time = None

        self.status = self.STATUS_CANCELLED
        self.save()

    def blacklist(self):
        self.status = self.STATUS_BLACKLISTED
        self.blacklisted_till = timezone.now() + timedelta(days=settings.PYTHONTASK_DAYS_DROP_FROM_BLACKLIST)
        self.save()

    def scored(self):
        self.status = self.STATUS_SCORED
        self.save()

    def mark_deleted(self):
        self.status = self.STATUS_DELETED
        self.taken_time = None
        self.blacklisted_till = None
        self.save()

    class Meta:
        unique_together = (("user", "task"),)

    def __unicode__(self):
        return unicode(self.task) + " (" + unicode(self.user) + ")"


class TaskGroupRelations(models.Model):
    task = models.ForeignKey(Task, db_index=False, null=False, blank=False)
    group = models.ForeignKey(Group, db_index=False, null=False, blank=False)

    position = models.IntegerField(db_index=False, null=False, blank=False, default=0)

    deleted = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    class Meta:
        unique_together = ("task", "group")

    def __unicode__(self):
        return ' '.join([unicode(self.task), unicode(self.group), unicode(self.position)])


def task_save_to_log_post_save(sender, instance, created, **kwargs):
    task_log = TaskLog()
    task_log_dict = copy.deepcopy(instance.__dict__)
    task_log_dict['id'] = None
    task_log.__dict__ = task_log_dict
    task_log.sended_notify = False
    task_log.save()
    task_log.groups.add(*instance.groups.all())

# post_save.connect(task_save_to_log_post_save, sender=Task)
