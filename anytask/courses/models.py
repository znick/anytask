# -*- coding: utf-8 -*-
import os
import json

from django.core.urlresolvers import reverse
from django.db import models
from datetime import datetime
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.db.models.signals import m2m_changed
from django.conf import settings
from django.db.models.signals import post_save

from groups.models import Group
from issues.model_issue_field import IssueField
from years.models import Year
from anyrb.common import RbReviewGroup

def add_group_with_extern(sender, instance, **kwargs):
    instance.add_group_with_extern()

class DefaultIssueFields(set):
    DEFAILT_USSUE_FIELDS_FIXTURE = os.path.join(settings.PROJECT_PATH, "issues", "fixtures", "initial_data.json")
    _default_issue_fields = set()
    _default_issue_fields_pks = set()

    def _get_default_issue_fields(self):
        default_issue_fields = set()
        default_issue_fields_pks = set()

        with open(self.DEFAILT_USSUE_FIELDS_FIXTURE) as fixture_fn:
            fixture = json.load(fixture_fn)
            for issue_field in fixture:
                default_issue_fields_pks.add(issue_field["pk"])

        default_issue_fields = set(IssueField.objects.filter(pk__in=default_issue_fields_pks))
        return default_issue_fields_pks, default_issue_fields

    def get_pks(self):
        if not self.__class__._default_issue_fields_pks:
            self.__class__._default_issue_fields_pks, self.__class__._default_issue_fields = self._get_default_issue_fields()
        return self.__class__._default_issue_fields_pks

    def get_issue_fields(self):
        if not self.__class__._default_issue_fields:
            self.__class__._default_issue_fields_pks, self.__class__._default_issue_fields = self._get_default_issue_fields()
        return self.__class__._default_issue_fields


class FilenameExtension(models.Model):
    name = models.CharField(max_length=10, db_index=False, null=False, blank=False)

    def __unicode__(self):
        return self.name


class Course(models.Model):

    TYPE_POTOK = 0
    TYPE_ONE_TASK_MANY_GROUP = 1
    TYPE_MANY_TASK_MANY_GROUP = 2
    TYPE_SPECIAL_COURSE = 3
    TYPE_SHAD_CPP = 4

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
        (TYPE_SPECIAL_COURSE,       _(u'Special Course')),
        (TYPE_SHAD_CPP,             _(u'Shad c++')),
    )

    type = models.IntegerField(max_length=1, choices=TYPES, db_index=True, null=True, blank=True, default=0)

    TAKE_POLICYS = (
        (TAKE_POLICY_SELF_TAKEN,                _(u'Self taken')),
        (TAKE_POLICY_SET_BY_TEACHER,            _(u'Set by teacher')),
        (TAKE_POLICY_ALL_TASKS_TO_ALL_STUDENTS, _(u'All tasks to all students')),
    )
    take_policy = models.IntegerField(max_length=1, choices=TAKE_POLICYS, db_index=True, null=True, blank=True, default=0)

    students = models.ManyToManyField(User, related_name='course_students_set', null=True, blank=True)
    teachers = models.ManyToManyField(User, related_name='course_teachers_set', null=True, blank=True)
    groups = models.ManyToManyField(Group, null=True, blank=True)

    issue_fields = models.ManyToManyField(IssueField, null=True, blank=True)

    max_users_per_task = models.IntegerField(null=True, blank=True, default=0)
    max_days_without_score = models.IntegerField(null=True, blank=True, default=0)
    max_tasks_without_score_per_student = models.IntegerField(null=True, blank=True, default=0)
    days_drop_from_blacklist = models.IntegerField(null=True, blank=True, default=0)

    contest_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    send_rb_and_contest_together = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    rb_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    gr_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    pdf_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    filename_extensions = models.ManyToManyField(FilenameExtension, related_name='filename_extensions_set', null=True, blank=True)

    full_transcript = models.BooleanField(db_index=False, null=False, blank=False, default=True)

    private = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

    can_be_chosen_by_extern = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    group_with_extern = models.ForeignKey(Group, related_name="course_with_extern", db_index=False, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.name)

    def get_absolute_url(self):
        return reverse('courses.views.course_page', args=[str(self.id)])

    def user_can_edit_course(self, user):
        if user.is_anonymous():
            return False
        if user.is_superuser:
            return True
        return self.user_is_teacher(user)

    def user_is_teacher(self, user):
        if user.is_superuser or user.is_staff:
            return True

        return self.teachers.filter(id=user.id).count() > 0

    def is_special_course(self):
        return self.type == Course.TYPE_SPECIAL_COURSE

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

        if self.students.filter(id=user.id).exists():
            return True

        return False

    def user_can_see_transcript(self, user, student):
        if user.is_anonymous():
            return not self.private and self.full_transcript
        if self.user_is_teacher(user):
            return True
        if self.full_transcript:
            return True
        else:
            return user.id == student.id

    def user_can_see_queue(self, user):
        if user.is_anonymous():
            return False
        if self.user_is_teacher(user):
            return True
        return False

    def save(self, *args, **kwargs):
        super(Course, self).save(*args, **kwargs)
        self.add_group_with_extern()

    def add_group_with_extern(self):
        if self.group_with_extern is None and self.can_be_chosen_by_extern:
            group, ok = Group.objects.get_or_create(year=self.year,name=u'%s - слушатели' % self.name)
            group.save()
            self.group_with_extern = group
            self.groups.add(group)
            self.save()

    def add_user_to_group_with_extern(self,user):
        self.add_group_with_extern()
        self.group_with_extern.students.add(user)

    def remove_user_from_group_with_extern(self,user):
         if self.group_with_extern is not None:
             self.group_with_extern.students.remove(user)

    def get_teachers(self):
        return self.teachers.all().order_by('last_name', 'first_name')

    def get_default_teacher(self, group):
        try:
            return DefaultTeacher.objects.filter(course=self).get(group=group).teacher
        except DefaultTeacher.DoesNotExist:
            return None

class DefaultTeacher(models.Model):
    teacher = models.ForeignKey(User, db_index=False, null=True, blank=True)
    course = models.ForeignKey(Course, db_index=True, null=False, blank=False)
    group = models.ForeignKey(Group, db_index=True, null=True, blank=True)

    def __unicode__(self):
        return u"|".join((self.course.name, self.group.name, self.teacher.username))

    class Meta:
        unique_together = (("course", "group"),)

def add_default_issue_fields(sender, instance, action, **kwargs):
    default_issue_fields = DefaultIssueFields()
    pk_set = kwargs.get("pk_set", set())
    if action not in ("post_add", "post_remove", "post_clear"):
        return

    if action in ("post_remove", "post_clear"):
        instance.issue_fields.add(*default_issue_fields.get_issue_fields())
        return

    if set(pk_set) == default_issue_fields.get_pks():
        return

    if action == "post_add":
        instance.issue_fields.remove(*default_issue_fields.get_issue_fields())
        return

def update_rb_review_group(sender, instance, created, **kwargs):
    course = instance
    if not course.rb_integrated:
        return

    rb_review_group_name = "teachers_{0}".format(course.id)
    rg = RbReviewGroup(rb_review_group_name)
    rg.create()
    teachers = set([teacher.username for teacher in course.teachers.all()])
    rg_users = set(rg.list())

    for rg_user in rg_users:
        if rg_user not in teachers:
            rg.user_del(rg_user)

    for teacher in teachers:
        if teacher not in rg_users:
            rg.user_add(teacher)

m2m_changed.connect(add_default_issue_fields, sender=Course.issue_fields.through)
post_save.connect(update_rb_review_group, sender=Course)
