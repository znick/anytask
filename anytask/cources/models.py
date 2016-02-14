from django.db import models
from datetime import datetime
from django.utils.translation import ugettext as _

from django.contrib.auth.models import User
from groups.models import Group
from years.models import Year


class Cource(models.Model):

    TYPE_POTOK = 0
    TYPE_ONE_TASK_MANY_GROUP = 1
    TYPE_MANY_TASK_MANY_GROUP = 2
    TYPE_SPECTIAL_COURCE = 3

    TAKE_POLICY_SELF_TAKEN = 0
    TAKE_POLICY_SET_BY_TEACHER = 1
    TAKE_POLICY_ALL_TASKS_TO_ALL_STUDENTS = 2

    name = models.CharField(max_length=254, db_index=True, null=False, blank=False)
    name_id = models.CharField(max_length=254, db_index=True, null=True, blank=True)

    information = models.TextField(db_index=False, null=True, blank=True)

    year = models.ForeignKey(Year, db_index=True, null=False, blank=False, default=datetime.now().year)

    is_active = models.BooleanField(db_index=True, null=False, blank=False, default=False)

    TYPES = (
        (TYPE_POTOK,                _(u'Potok')),
        (TYPE_ONE_TASK_MANY_GROUP,  _(u'OneTasksManyGroup')),
        (TYPE_MANY_TASK_MANY_GROUP, _(u'ManyTasksManyGroup')),
        (TYPE_SPECTIAL_COURCE,      _(u'Special Course')),
    )
    type = models.IntegerField(max_length=1, choices=TYPES, db_index=True, null=True, blank=True, default=0)

    TAKE_POLICYS = (
        (TAKE_POLICY_SELF_TAKEN,                _(u'Self taken')),
        (TAKE_POLICY_SET_BY_TEACHER,            _(u'Set by teacher')),
        (TAKE_POLICY_ALL_TASKS_TO_ALL_STUDENTS, _(u'All tasks to all students')),
    )
    take_policy = models.IntegerField(max_length=1, choices=TAKE_POLICYS, db_index=True, null=True, blank=True, default=0)

    students = models.ManyToManyField(User, related_name='cource_students_set', null=True, blank=True)
    teachers = models.ManyToManyField(User, related_name='cource_teachers_set', null=True, blank=True)
    groups = models.ManyToManyField(Group, null=True, blank=True)

    max_users_per_task = models.IntegerField(null=True, blank=True, default=0)
    max_days_without_score = models.IntegerField(null=True, blank=True, default=0)
    max_tasks_without_score_per_student = models.IntegerField(null=True, blank=True, default=0)
    days_drop_from_blacklist = models.IntegerField(null=True, blank=True, default=0)

    rb_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    private = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    easy_ci = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

    def __unicode__(self):
        return unicode(self.name)

    def user_can_edit_cource(self, user):
        if user.is_anonymous():
            return False
        if user.is_superuser:
            return True
        return self.user_is_teacher(user)

    def user_is_teacher(self, user):
        if user.is_superuser:
            return True

        return self.teachers.filter(id=user.id).count() > 0

    def is_special_course(self):
        return self.type == Cource.TYPE_SPECTIAL_COURCE

    def get_user_group(self, user):
        for group in self.groups.filter(students=user):
            return group
        return None

    def user_is_attended(self, user):
        if user.is_anonymous():
            return False

        if self.user_is_teacher(user):
            return True

        if self.get_user_group(user):
            return True

        if self.students.filter(id=user.id).count() > 0:
            return True

        return False


