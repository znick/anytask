# coding: utf-8

from django.db import models
from datetime import datetime
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save, pre_delete

from courses.models import Course
from groups.models import Group

from django.db.models import Q, Max

from django.contrib.auth.models import User

from datetime import timedelta
import copy

class Task(models.Model):
    title = models.CharField(max_length=191, db_index=True, null=True, blank=True)
    course = models.ForeignKey(Course, db_index=True, null=False, blank=False)
    group = models.ForeignKey(Group, db_index=False, null=True, blank=True, default=None)
    groups = models.ManyToManyField(Group, null=False, blank=False, related_name='groups_set')

    weight = models.IntegerField(db_index=True, null=False, blank=False, default=0)

    is_hidden = models.BooleanField(db_index=True, null=False, blank=False, default=False)

    parent_task = models.ForeignKey('self', db_index=True, null=True, blank=True, related_name='children')

    task_text = models.TextField(null=True, blank=True, default=None)

    score_max = models.IntegerField(db_index=True, null=False, blank=False, default=0)

    contest_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    rb_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    TYPE_FULL = 'All'
    TYPE_SIMPLE = 'Only mark'
    TYPE_SEMINAR = 'Seminar'
    TYPE_MATERIAL = 'Material'
    TASK_TYPE_CHOICES = (
        (TYPE_FULL, _('s_obsuzhdeniem')),
        (TYPE_SIMPLE, _('tolko_ocenka')),
        (TYPE_MATERIAL, _('material')),
        (TYPE_SEMINAR, _('seminar')),
    )
    type = models.CharField(db_index=False, max_length=128, choices=TASK_TYPE_CHOICES, default=TYPE_FULL)

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)
    deadline_time = models.DateTimeField(auto_now=False, null=True, default=None)

    updated_by = models.ForeignKey(User, db_index=False, null=True, blank=True)

    contest_id = models.IntegerField(db_index=True, null=False, blank=False, default=0)
    problem_id = models.CharField(max_length=128, db_index=True, null=True, blank=True)

    send_to_users = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    sended_notify = models.BooleanField(db_index=True, null=False, blank=False, default=True)

    one_file_upload = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    accepted_after_contest_ok = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    not_score_deadline = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    def __unicode__(self):
        return unicode(self.title)

    def user_can_take_task(self, user):
        course = self.course

        if user.is_anonymous():
            return (False, '')

        if self.is_hidden:
            return (False, '')

        if not self.course.groups.filter(students=user).count():
            return (False, u'')

        if course.max_users_per_task:
            if TaskTaken.objects.filter(task=self).filter(Q( Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED))).count() >= course.max_users_per_task:
                return (False, u'Задача не может быть взята более чем %d студентами' % course.max_users_per_task)

        if course.max_tasks_without_score_per_student:
            if TaskTaken.objects.filter(user=user).filter(status=TaskTaken.STATUS_TAKEN).count() >= course.max_tasks_without_score_per_student:
                return (False, u'')

        if Task.objects.filter(parent_task=self).count() > 0:
            return (False, u'')

        if TaskTaken.objects.filter(task=self).filter(user=user).filter(Q( Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED))).count() != 0:
            return (False, u'')

        if self.parent_task is not None:
            tasks = Task.objects.filter(parent_task=self.parent_task)
            if TaskTaken.objects.filter(user=user).filter(task__in=tasks).exclude(status=TaskTaken.STATUS_CANCELLED).count() > 0:
                return (False, u'')

        try:
            task_taken = TaskTaken.objects.filter(task=self).filter(user=user).get(status=TaskTaken.STATUS_BLACKLISTED)
            black_list_expired_date = task_taken.update_time + timedelta(days=course.days_drop_from_blacklist)
            return (False, u'Вы сможете взять эту задачу с %s' % black_list_expired_date.strftime("%d.%m.%Y"))
        except TaskTaken.DoesNotExist:
            pass

        if TaskTaken.objects.filter(task=self).filter(user=user).filter(status=TaskTaken.STATUS_SCORED).count() != 0:
            return (False, u'')

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

        if not self.rb_integrated:
            return False

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
        return TaskTaken.objects.filter(task=self).filter(Q( Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_SCORED)))

    def add_user_properties(self, user):
        self.can_take = self.user_can_take_task(user)
        self.can_cancel = self.user_can_cancel_task(user)
        self.can_score = self.user_can_score_task(user)
        self.can_pass = self.user_can_pass_task(user)
        self.is_shown = not self.is_hidden or self.course.user_is_teacher(user)

    def has_issue_access(self):
        return self.type not in [self.TYPE_SIMPLE, self.TYPE_MATERIAL]

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
                max_position = TaskGroupRelations.objects.filter(group=group).exclude(id=task_related.id)\
                    .aggregate(Max('position'))['position__max']
                task_related.position = max_position + 1 if max_position is not None else 0
            else:
                task_related.deleted = False
            task_related.save()


class TaskLog(models.Model):
    title = models.CharField(max_length=191, db_index=True, null=True, blank=True)
    course = models.ForeignKey(Course, db_index=False, null=False, blank=False)
    group = models.ForeignKey(Group, db_index=False, null=True, blank=True, default=None)
    groups = models.ManyToManyField(Group, null=False, blank=False, related_name='groups_log_set')

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

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)
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

    TASK_TAKEN_STATUSES = (
        (STATUS_TAKEN,          u'Task taken'),
        (STATUS_CANCELLED,      u'Task cancelled'),
        (STATUS_BLACKLISTED,    u'Task blacklisted'),
        (STATUS_SCORED,         u'Task scored'),
        (STATUS_DELETED,        u'TaskTaken deleted')
    )
    status = models.IntegerField(max_length=1, choices=TASK_TAKEN_STATUSES, db_index=True, null=False, blank=False, default=0)

    EDIT = 'EDIT'
    QUEUE = 'QUEUE'
    OK = 'OK'
    STATUS_CHECK_CHOICES = (
        (EDIT, u'Дорешивание'),
        (QUEUE, u'Ожидает проверки'),
        (OK, u'Задача зачтена и/или больше не принимается'),
    )
    status_check = models.CharField(db_index=True, max_length=5, choices=STATUS_CHECK_CHOICES, default=EDIT)

    teacher = models.ForeignKey(User, db_index=True, null=True, blank=False, default=None, related_name='teacher')

    score = models.FloatField(db_index=False, null=False, blank=False, default=0)
    scored_by = models.ForeignKey(User, db_index=True, null=True, blank=True, related_name='task_taken_scored_by_set')

    teacher_comments = models.TextField(db_index=False, null=True, blank=True, default='')

    id_issue_gr_review = models.IntegerField(db_index=True, null=True, blank=False, default=None)
    pdf = models.FileField(upload_to="pdf_review", db_index=True, null=True, blank=False, default=None)

    pdf_update_time = models.DateTimeField(default=datetime.now)
    gr_review_update_time = models.DateTimeField(default=datetime.now)

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

    class Meta:
        unique_together = (("user", "task"),)

    def __unicode__(self):
        return unicode(self.task) + " (" + unicode(self.user) + ")"

    def user_can_change_status(self, user, status):
        if user.is_anonymous():
            return False
        if self.task.course.user_is_teacher(user):
            return True
        if user.id != self.user.id:
            return False
        if status == self.OK:
            return  self.status_check == self.OK
        else:
            return  self.status_check != self.OK

    def user_can_change_teacher(self, user):
        if user.is_anonymous():
            return False
        if self.task.course.user_is_teacher(user):
            return True
        return False


class TaskTakenLog(models.Model):
    user = models.ForeignKey(User, db_index=False, null=False, blank=False)
    task = models.ForeignKey(Task, db_index=False, null=False, blank=False)

    status = models.IntegerField(max_length=1, choices=TaskTaken.TASK_TAKEN_STATUSES, db_index=True, null=False, blank=False, default=0)

    score = models.IntegerField(db_index=False, null=False, blank=False, default=0)
    scored_by = models.ForeignKey(User, db_index=False, null=True, blank=True, related_name='task_taken_log_scored_by_set')

    teacher_comments = models.TextField(db_index=False, null=True, blank=True, default='')

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

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
    task_log_dict  = copy.deepcopy(instance.__dict__)
    task_log_dict['id'] = None
    task_log.__dict__ = task_log_dict
    task_log.sended_notify = False
    task_log.save()
    task_log.groups.add(*instance.groups.all())

def task_taken_save_to_log_post_save(sender, instance, created, **kwargs):
    task_taken_log = TaskTakenLog()
    task_taken_log_dict  = copy.deepcopy(instance.__dict__)
    task_taken_log_dict['id'] = None
    task_taken_log.__dict__ = task_taken_log_dict
    task_taken_log.save()

def task_taken_save_to_log_pre_delete(sender, instance, **kwargs):
    task_taken_log = TaskTakenLog()
    task_taken_log_dict  = copy.deepcopy(instance.__dict__)
    task_taken_log_dict['id'] = None
    task_taken_log.__dict__ = task_taken_log_dict
    task_taken_log.scored_by = None
    task_taken_log.status = TaskTaken.STATUS_DELETED
    task_taken_log.save()


# post_save.connect(task_save_to_log_post_save, sender=Task)
post_save.connect(task_taken_save_to_log_post_save, sender=TaskTaken)
pre_delete.connect(task_taken_save_to_log_pre_delete, sender=TaskTaken)
