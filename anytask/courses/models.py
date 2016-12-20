# -*- coding: utf-8 -*-
import os
import json

from django.core.urlresolvers import reverse
from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from django.db.models.signals import m2m_changed
from django.conf import settings
from django.db.models.signals import post_save
from django.db.models import Q

from groups.models import Group
from issues.model_issue_status import IssueStatusSystem
from issues.model_issue_field import IssueField
from years.models import Year
from anyrb.common import RbReviewGroup


def add_group_with_extern(sender, instance, **kwargs):
    instance.add_group_with_extern()


class DefaultIssueFields(set):
    _DEFAULT_ISSUE_FIELDS_PKS = set([1, 2, 3, 4, 5, 6, 7, 8, 9])
    _DEFAULT_RB_ISSUE_FIELDS_PKS = set([10])
    _DEFAULT_CNTST_ISSUE_FIELDS_PKS = set([11])
    _default_issue_fields = set()
    _default_issue_fields_pks = set()
    _course_rb_integrated = False
    _course_contest_integrated = False

    def set_integrated(self, rb_integrated=False, contest_integrated=False):
        self._course_rb_integrated = rb_integrated
        self._course_contest_integrated = contest_integrated

    def _get_default_issue_fields(self):
        rb_pk = self._DEFAULT_RB_ISSUE_FIELDS_PKS if self._course_rb_integrated else set()
        contest_pk = self._DEFAULT_CNTST_ISSUE_FIELDS_PKS if self._course_contest_integrated else set()

        default_issue_fields_pks = self._DEFAULT_ISSUE_FIELDS_PKS | rb_pk | contest_pk

        default_issue_fields = set(IssueField.objects.filter(pk__in=default_issue_fields_pks))
        return default_issue_fields_pks, default_issue_fields

    def get_pks(self):
        self.__class__._default_issue_fields_pks, self.__class__._default_issue_fields = self._get_default_issue_fields()
        return self.__class__._default_issue_fields_pks

    def get_issue_fields(self):
        self.__class__._default_issue_fields_pks, self.__class__._default_issue_fields = self._get_default_issue_fields()
        return self.__class__._default_issue_fields

    def get_deleted_pks(self):
        rb_pk = self._DEFAULT_RB_ISSUE_FIELDS_PKS if not self._course_rb_integrated else set()
        contest_pk = self._DEFAULT_CNTST_ISSUE_FIELDS_PKS if not self._course_contest_integrated else set()

        return rb_pk | contest_pk

    def get_deleted_issue_fields(self):
        return set(IssueField.objects.filter(pk__in=self.get_deleted_pks()))


class FilenameExtension(models.Model):
    name = models.CharField(max_length=10, db_index=False, null=False, blank=False)

    def __unicode__(self):
        return self.name


class MarkField(models.Model):
    name = models.CharField(max_length=191, db_index=True, null=False, blank=False)
    name_int = models.IntegerField(db_index=False, null=False, blank=False, default=0)

    def __unicode__(self):
        return self.name if self.name else '--'


class CourseMarkSystem(models.Model):
    name = models.CharField(max_length=191, db_index=False, null=False, blank=False)
    marks = models.ManyToManyField(MarkField, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.name)


class Course(models.Model):

    name = models.CharField(max_length=191, db_index=True, null=False, blank=False)
    name_id = models.CharField(max_length=191, db_index=True, null=True, blank=True)

    information = models.TextField(db_index=False, null=True, blank=True)

    year = models.ForeignKey(Year, db_index=True, null=False, blank=False, default=datetime.now().year)

    is_active = models.BooleanField(db_index=True, null=False, blank=False, default=False)

    teachers = models.ManyToManyField(User, related_name='course_teachers_set', null=True, blank=True)
    groups = models.ManyToManyField(Group, null=True, blank=True)

    issue_fields = models.ManyToManyField(IssueField, null=True, blank=True)

    contest_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    send_rb_and_contest_together = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    rb_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    send_to_contest_from_users = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    filename_extensions = models.ManyToManyField(FilenameExtension, related_name='filename_extensions_set', null=True, blank=True)

    full_transcript = models.BooleanField(db_index=False, null=False, blank=False, default=True)

    private = models.BooleanField(db_index=False, null=False, blank=False, default=True)

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

    can_be_chosen_by_extern = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    group_with_extern = models.ForeignKey(Group, related_name="course_with_extern", db_index=False, null=True, blank=True)

    mark_system = models.ForeignKey(CourseMarkSystem, db_index=False, null=True, blank=True)


    show_accepted_after_contest_ok = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    default_accepted_after_contest_ok = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    show_task_one_file_upload = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    default_task_one_file_upload = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    default_task_send_to_users = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    issue_status_system = models.ForeignKey(IssueStatusSystem, db_index=False, null=False, blank=False, default=1)

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
        return self.teachers.order_by('last_name', 'first_name')

    def get_default_teacher(self, group):
        try:
            return DefaultTeacher.objects.filter(course=self).get(group=group).teacher
        except DefaultTeacher.DoesNotExist:
            return None

    def is_rb_integrated(self):
        return self.rb_integrated or self.task_set.filter(rb_integrated=True).count()

    def is_contest_integrated(self):
        return self.contest_integrated or self.task_set.filter(contest_integrated=True).count()


class DefaultTeacher(models.Model):
    teacher = models.ForeignKey(User, db_index=False, null=True, blank=True)
    course = models.ForeignKey(Course, db_index=True, null=False, blank=False)
    group = models.ForeignKey(Group, db_index=True, null=True, blank=True)

    def __unicode__(self):
        return u"|".join((self.course.name, self.group.name, self.teacher.username))

    class Meta:
        unique_together = (("course", "group"),)


class StudentCourseMark(models.Model):
    student = models.ForeignKey(User, db_index=True, null=False, blank=False)
    course = models.ForeignKey(Course, db_index=False, null=False, blank=False)
    group = models.ForeignKey(Group, db_index=False, null=True, blank=True)
    mark = models.ForeignKey(MarkField, db_index=False, null=True, blank=True)

    teacher = models.ForeignKey(User, related_name='teacher_change_mark', db_index=False, null=True, blank=True)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

    def __unicode__(self):
        return unicode(self.mark)

    class Meta:
        unique_together = (("student", "course", "group"),)


def add_default_issue_fields(sender, instance, action, **kwargs):
    default_issue_fields = DefaultIssueFields()
    default_issue_fields.set_integrated(instance.rb_integrated, instance.contest_integrated)
    pk_set = kwargs.get("pk_set", set())

    if action not in ("post_add", "post_remove", "post_clear"):
        return

    if action in ("post_remove", "post_clear"):
        if pk_set and set(pk_set) == default_issue_fields.get_deleted_pks():
            return

        instance.issue_fields.add(*default_issue_fields.get_issue_fields())
        return

    if action == "post_add":
        if pk_set and set(pk_set) == default_issue_fields.get_pks():
            return

        instance.issue_fields.remove(*default_issue_fields.get_deleted_issue_fields())
        return

def update_rb_review_group(sender, instance, created, **kwargs):
    course = instance

    if not course.is_rb_integrated():
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
