# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.translation import ugettext as _
from django import forms

from datetime import datetime

from years.common import get_current_year
from groups.models import Group
from courses.models import Course
from issues.models import Issue
from issues.model_issue_status import IssueStatus


from anytask.storage import OverwriteStorage

import os
import django_filters


def get_upload_path(instance, filename):
    return os.path.join('images', 'user_%d' % instance.user.id, filename)


class UserProfile(models.Model):
    user = models.ForeignKey(User, db_index=True, null=False, blank=False, unique=True)
    second_name = models.CharField(max_length=128, db_index=True, null=True, blank=True)

    avatar = models.ImageField('profile picture', upload_to=get_upload_path, blank=True, null=True, storage=OverwriteStorage())
    birth_date = models.DateField(blank=True, null=True)

    info = models.TextField(default="", blank=True, null=True)

    unit = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    position = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    academic_degree = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    academic_title = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)


    ya_uid = models.IntegerField(null=True, blank=True)
    ya_login = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    ya_contest_oauth = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    ya_passport_oauth = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    def is_current_year_student(self):
        return Group.objects.filter(year=get_current_year()).filter(students=self.user).count() > 0

    def __unicode__(self):
            return unicode(self.user)


class IssueFilterStudent(django_filters.FilterSet):
    courses = django_filters.MultipleChoiceFilter(label=u'Курс', name='task__course', widget=forms.CheckboxSelectMultiple)
    responsible = django_filters.MultipleChoiceFilter(label=u'Преподаватели', widget=forms.CheckboxSelectMultiple)
    status_field = django_filters.MultipleChoiceFilter(label=u'Статус', widget=forms.CheckboxSelectMultiple)
    update_time = django_filters.DateRangeFilter(label=u'Дата последнего изменения')

    def set_user(self, user):
        groups = user.group_set.all()
        courses = Course.objects.filter(groups__in=groups)

        course_choices = []
        teacher_set = set()
        status_set = set()
        for course in courses:
            course_choices.append((course.id, _(course.name)))

            for teacher in course.get_teachers():
                teacher_set.add(teacher)

            for status in course.issue_status_system.statuses.all():
                status_set.add(status)

        self.filters['courses'].field.choices = tuple(course_choices)

        teacher_choices = [(teacher.id, _(teacher.get_full_name())) for teacher in teacher_set]
        self.filters['responsible'].field.choices = tuple(teacher_choices)

        status_choices = [(status.id, _(status.name)) for status in status_set]
        for status_id in sorted(IssueStatus.HIDDEN_STATUSES.values(), reverse=True):
            status_field = IssueStatus.objects.get(pk=status_id)
            status_choices.insert(0, (status_field.id, _(status_field.name)))
        self.filters['status_field'].field.choices = tuple(status_choices)

    class Meta:
        model = Issue
        fields = ['status_field', 'responsible', 'courses', 'update_time']


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
