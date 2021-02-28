# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import m2m_changed
from django.db.models.signals import post_save

from groups.models import Group
from issues.model_issue_status import IssueStatusSystem
from issues.model_issue_field import IssueField
from years.models import Year
from anyrb.common import RbReviewGroup

import logging
logger = logging.getLogger('django.request')


def add_group_with_extern(sender, instance, **kwargs):
    instance.add_group_with_extern()


class DefaultIssueFields(set):
    _DEFAULT_ISSUE_FIELDS_PKS = {1, 2, 3, 4, 5, 6, 7, 8, 9}
    _DEFAULT_RB_ISSUE_FIELDS_PKS = {10}
    _DEFAULT_CNTST_ISSUE_FIELDS_PKS = {11}
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
        self.__class__._default_issue_fields_pks, \
            self.__class__._default_issue_fields = self._get_default_issue_fields()
        return self.__class__._default_issue_fields_pks

    def get_issue_fields(self):
        self.__class__._default_issue_fields_pks, \
            self.__class__._default_issue_fields = self._get_default_issue_fields()
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
    name_int = models.IntegerField(db_index=False, null=False, blank=False, default=-1)

    def __unicode__(self):
        return self.name if self.name else '--'

    class Meta:
        ordering = ['-name_int']


class CourseMarkSystem(models.Model):
    name = models.CharField(max_length=191, db_index=False, null=False, blank=False)
    marks = models.ManyToManyField(MarkField, blank=True)

    def __unicode__(self):
        return unicode(self.name)


class Course(models.Model):
    name = models.CharField(max_length=191, db_index=True, null=False, blank=False)
    name_id = models.CharField(max_length=191, db_index=True, null=True, blank=True)

    information = models.TextField(db_index=False, null=True, blank=True)

    year = models.ForeignKey(Year, db_index=True, null=False, blank=False, default=timezone.now().year)

    is_active = models.BooleanField(db_index=True, null=False, blank=False, default=False)

    teachers = models.ManyToManyField(User, related_name='course_teachers_set', blank=True)
    groups = models.ManyToManyField(Group, blank=True)

    issue_fields = models.ManyToManyField(IssueField, blank=True)

    contest_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    send_rb_and_contest_together = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    rb_integrated = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    take_mark_from_contest = models.BooleanField(default=False)

    send_to_contest_from_users = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    filename_extensions = models.ManyToManyField(
        FilenameExtension, related_name='filename_extensions_set', blank=True
    )

    full_transcript = models.BooleanField(db_index=False, null=False, blank=False, default=True)

    private = models.BooleanField(db_index=False, null=False, blank=False, default=True)

    added_time = models.DateTimeField(auto_now_add=True)  # remove default=timezone.now
    update_time = models.DateTimeField(auto_now=True)  # remove default=timezone.now

    can_be_chosen_by_extern = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    group_with_extern = models.ForeignKey(
        Group, related_name="course_with_extern", db_index=False, null=True, blank=True
    )

    mark_system = models.ForeignKey(CourseMarkSystem, db_index=False, null=True, blank=True)

    show_accepted_after_contest_ok = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    default_accepted_after_contest_ok = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    show_task_one_file_upload = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    default_task_one_file_upload = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    default_task_send_to_users = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    issue_status_system = models.ForeignKey(IssueStatusSystem, db_index=False, null=False, blank=False, default=1)

    is_python_task = models.BooleanField(db_index=False, null=False, blank=False, default=False)
    max_students_per_task = models.IntegerField(null=False, blank=False, default=0)
    max_incomplete_tasks = models.IntegerField(null=False, blank=False, default=0)
    max_not_scored_tasks = models.IntegerField(null=False, blank=False, default=0)

    has_attendance_log = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    show_contest_run_id = models.BooleanField(db_index=False, null=False, blank=False, default=True)

    def __unicode__(self):
        return unicode(self.name)

    def get_full_name(self):
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

        return self.teachers.filter(id=user.id).exists()

    def user_is_student(self, user):
        return self.groups.filter(students=user).exists()

    def get_user_group(self, user):
        for group in self.groups.filter(students=user):
            return group
        return None

    def user_is_attended(self, user):
        if user.is_anonymous():
            return False

        if self.user_is_teacher(user):
            return True

        if self.user_is_student(user):
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

    def user_can_see_contest_run_id(self, user):
        if user.is_anonymous():
            return False
        if self.send_to_contest_from_users and (self.user_is_teacher(user) or self.show_contest_run_id):
            return True
        return False

    def user_can_see_attendance_log(self, user):
        if user.is_anonymous():
            return False
        return self.has_attendance_log and self.user_is_teacher(user)

    def save(self, *args, **kwargs):
        super(Course, self).save(*args, **kwargs)
        self.add_group_with_extern()

    def add_group_with_extern(self):
        if self.group_with_extern is None and self.can_be_chosen_by_extern:
            group, ok = Group.objects.get_or_create(year=self.year, name=u'%s - слушатели' % self.name)
            group.save()
            self.group_with_extern = group
            self.groups.add(group)
            self.save()

    def add_user_to_group_with_extern(self, user):
        self.add_group_with_extern()
        self.group_with_extern.students.add(user)

    def remove_user_from_group_with_extern(self, user):
        if self.group_with_extern is not None:
            self.group_with_extern.students.remove(user)

    def get_teachers(self):
        return self.teachers.order_by('last_name', 'first_name')

    def get_students(self):
        return User.objects\
            .filter(group__in=self.groups.all())\
            .distinct()\
            .order_by('last_name', 'first_name')

    def get_default_teacher(self, group):
        try:
            return DefaultTeacher.objects.filter(course=self).get(group=group).teacher
        except DefaultTeacher.DoesNotExist:
            return None

    def is_rb_integrated(self):
        return self.rb_integrated

    def is_contest_integrated(self):
        return self.contest_integrated or self.task_set.filter(contest_integrated=True).exists()


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
    mark = models.ForeignKey(MarkField, db_index=False, null=True, blank=True)

    teacher = models.ForeignKey(User, related_name='teacher_change_mark', db_index=False, null=True, blank=True)
    update_time = models.DateTimeField(auto_now=True)  # remove default=timezone.now

    def __unicode__(self):
        return unicode(self.mark)

    class Meta:
        unique_together = (("student", "course"),)


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
    logger.info("update_rb_review_group: '%s'", course)

    if not course.is_rb_integrated():
        return

    rb_review_group_name = "teachers_{0}".format(course.id)
    rg = RbReviewGroup(rb_review_group_name)
    rg.create()
    teachers = set([teacher.username for teacher in course.teachers.all()])
    rg_users = set(rg.list())

    logger.info("Course: '%s', teachets '%s', rg_users '%s'", course, teachers, rg_users)

    for rg_user in rg_users:
        if rg_user not in teachers:
            logger.info("Course: '%s', user_del '%s'", course, rg_user)
            rg.user_del(rg_user)

    for teacher in teachers:
        if teacher not in rg_users:
            logger.info("Course: '%s', user_add '%s'", course, teacher)
            rg.user_add(teacher)


m2m_changed.connect(add_default_issue_fields, sender=Course.issue_fields.through)
post_save.connect(update_rb_review_group, sender=Course)
