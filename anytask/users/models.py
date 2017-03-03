# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.translation import ugettext as _
from django import forms

from datetime import datetime
from collections import defaultdict

from years.common import get_current_year
from groups.models import Group
from courses.models import Course
from mail.models import Message

from colorfield.fields import ColorField

from anytask.storage import OverwriteStorage

import os
import django_filters
import copy

import logging

logger = logging.getLogger('django.request')


def get_upload_path(instance, filename):
    return os.path.join('images', 'user_%d' % instance.user.id, filename)


class UserStatus(models.Model):
    COLOR_DEFAULT = '#818A91'

    STATUS_ACTIVE = 'active'
    STATUS_EXTRAMURAL = 'extramural'
    STATUS_FULLTIME = 'fulltime'
    STATUS_NOT_ACTIVE = 'not_active'
    STATUS_ACADEMIC = 'academic'

    USER_STATUSES = (
        (STATUS_ACTIVE, _(STATUS_ACTIVE)),
        (STATUS_EXTRAMURAL, _(STATUS_EXTRAMURAL)),
        (STATUS_FULLTIME, _(STATUS_FULLTIME)),
        (STATUS_NOT_ACTIVE, _(STATUS_NOT_ACTIVE)),
        (STATUS_ACADEMIC, _(STATUS_ACADEMIC))
    )

    TYPE_ACTIVITY = 'activity'
    TYPE_FILIAL = 'filial'
    TYPE_EDUCATION_FORM = 'education_form'

    TYPE_STATUSES = (
        (TYPE_ACTIVITY, _(u'Статус студента')),
        (TYPE_FILIAL, _(u'Филлиал')),
        # (TYPE_EDUCATION_FORM, _(u'Форма обучения')),
    )

    name = models.CharField(max_length=254, db_index=True, null=False, blank=False)
    type = models.CharField(max_length=191, db_index=False, null=True, blank=True, choices=TYPE_STATUSES)
    tag = models.CharField(max_length=254, db_index=False, null=True, blank=True, choices=USER_STATUSES)
    color = ColorField(default=COLOR_DEFAULT)

    def __unicode__(self):
        return u'{0}'.format(self.name)


class UserProfile(models.Model):
    user = models.ForeignKey(User, db_index=True, null=False, blank=False, unique=True, related_name='profile')
    second_name = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    user_status = models.ManyToManyField(UserStatus, db_index=True, null=True, blank=True,
                                         related_name='users_by_status')

    avatar = models.ImageField('profile picture', upload_to=get_upload_path, blank=True, null=True,
                               storage=OverwriteStorage())
    birth_date = models.DateField(blank=True, null=True)

    info = models.TextField(default="", blank=True, null=True)

    phone = models.CharField(max_length=128, null=True, blank=True)

    unit = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    position = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    academic_degree = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    academic_title = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    show_email = models.BooleanField(db_index=False, null=False, blank=False, default=True)
    send_my_own_events = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    unread_messages = models.ManyToManyField(Message, null=True, blank=True, related_name='unread_messages')
    deleted_messages = models.ManyToManyField(Message, null=True, blank=True, related_name='deleted_messages')
    send_notify_messages = models.ManyToManyField(Message, null=True, blank=True, related_name='send_notify_messages')

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

    updated_by = models.ForeignKey(User, db_index=False, null=True, blank=True)

    login_via_yandex = models.BooleanField(db_index=False, null=False, blank=False, default=True)

    ya_uid = models.IntegerField(null=True, blank=True)
    ya_login = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    ya_contest_uid = models.IntegerField(null=True, blank=True)
    ya_contest_oauth = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    ya_contest_login = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    ya_passport_uid = models.IntegerField(null=True, blank=True)
    ya_passport_oauth = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    ya_passport_login = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    ya_passport_email = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    def is_current_year_student(self):
        return Group.objects.filter(year=get_current_year()).filter(students=self.user).count() > 0

    def __unicode__(self):
        return unicode(self.user)

    def is_active(self):
        for status in self.user_status.all():
            if status.tag == 'not_active' or status.tag == 'academic':
                return False
        return True

    def set_status(self, new_status):
        if not isinstance(new_status, UserStatus):
            new_status = UserStatus.objects.get(id=new_status)

        if new_status.type:
            self.user_status.remove(*self.user_status.filter(type=new_status.type))

        self.user_status.add(new_status)

    def get_unread_count(self):
        return self.unread_messages.exclude(id__in=self.deleted_messages.all()).count()

    def can_sync_contest(self):
        for course in Course.objects.filter(is_active=True):
            if course.get_user_group(self.user) and course.send_to_contest_from_users:
                return True
        return False


class UserProfileLog(models.Model):
    user = models.ForeignKey(User, db_index=True, null=False, blank=False, related_name='profiles_logs_by_user')
    second_name = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    user_status = models.ManyToManyField(UserStatus, db_index=True, null=True, blank=True)

    avatar = models.ImageField('profile picture', upload_to=get_upload_path, blank=True, null=True,
                               storage=OverwriteStorage())
    birth_date = models.DateField(blank=True, null=True)

    info = models.TextField(default="", blank=True, null=True)

    unit = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    position = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    academic_degree = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    academic_title = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    show_email = models.BooleanField(db_index=False, null=False, blank=False, default=True)
    send_my_own_events = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

    ya_uid = models.IntegerField(null=True, blank=True)
    ya_login = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    ya_contest_oauth = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    ya_passport_oauth = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    updated_by = models.ForeignKey(User, db_index=False, null=True, blank=True)

    def is_current_year_student(self):
        return Group.objects.filter(year=get_current_year()).filter(students=self.user).count() > 0

    def __unicode__(self):
        return unicode(self.user)

class CustomMethodFilter(django_filters.MethodFilter):
    def __init__(self, *args, **kwargs):
        self.field_class = kwargs.pop('field_class', forms.Field)

        super(CustomMethodFilter, self).__init__(*args, **kwargs)


class UserProfileFilter(django_filters.FilterSet):
    courses = CustomMethodFilter(label=u'<strong>{0}</strong>'.format(_(u'Курс')),
                                 action='filter_course',
                                 widget=forms.SelectMultiple,
                                 field_class=forms.MultipleChoiceField)
    groups = CustomMethodFilter(label=u'<strong>{0}</strong>'.format(_(u'Группа')),
                                action='filter_group',
                                widget=forms.SelectMultiple,
                                field_class=forms.MultipleChoiceField)
    user_status_activity = django_filters.MultipleChoiceFilter(
        label=u'<strong>{0}</strong>'.format(_(u'Статус студента')),
        name='user_status',
        widget=forms.SelectMultiple)
    user_status_filial = django_filters.MultipleChoiceFilter(label=u'<strong>{0}</strong>'.format(_(u'Филиал')),
                                                             name='user_status',
                                                             widget=forms.SelectMultiple)

    @property
    def qs(self):
        if not hasattr(self, '_qs'):
            qs = super(UserProfileFilter, self).qs
            if not hasattr(self, '_users_info'):
                qs_filter = {}

                if u'courses' in self.data:
                    qs_filter['user__group__course__id__in'] = self.data.getlist(u'courses')
                if u'groups' in self.data:
                    qs_filter['user__group__id__in'] = self.data.getlist(u'groups')

                users_info = {}
                for info in qs.filter(**qs_filter).values(
                        'id',
                        'user__id',
                        'user__username',
                        'user__email',
                        'user__last_name',
                        'user__first_name',
                        'user_status__id',
                        'user_status__name',
                        'user_status__color',
                        # 'user__group__course__id',
                        # 'user__group__course__name',
                        # 'user__group__course__is_active'
                ):
                    if info['user__id'] not in users_info:
                        users_info[info['user__id']] = defaultdict(dict)
                        users_info[info['user__id']]['id_profile'] = info['id']
                        users_info[info['user__id']]['username'] = info['user__username']
                        users_info[info['user__id']]['email'] = info['user__email']
                        users_info[info['user__id']]['last_name'] = info['user__last_name']
                        users_info[info['user__id']]['first_name'] = info['user__first_name']
                    if info['user_status__id']:
                        users_info[info['user__id']]['statuses'][info['user_status__id']] = {
                            'name': info['user_status__name'],
                            'color': info['user_status__color'],
                        }
                    # users_info[info['user__id']]['courses'][info['user__group__course__id']] = {
                    #     'name': info['user__group__course__name']
                    # }
                self.users_info = users_info
        return self._qs

    def filter_course(self, qs, value):
        # if not hasattr(self, '_qs'):
        #     if value and qs:
        #         return qs.filter(user__group__course__id__in=value).distinct()
        return qs

    def filter_group(self, qs, value):
        # if not hasattr(self, '_qs'):
        #     if value and qs:
        #         return qs.filter(user__group__id__in=value).distinct()
        return qs

    def set(self):
        self.courses_qs = Course.objects.filter(is_active=True)
        courses_choices = [(course.id, unicode(course)) for course in self.courses_qs]
        self.filters['courses'].field.choices = tuple(courses_choices)

        self.groups_qs = Group.objects.all()
        groups = [(group.id, unicode(group)) for group in self.groups_qs]
        self.filters['groups'].field.choices = tuple(groups)

        activity_choices = [(status.id, status.name) for status in UserStatus.objects.filter(type='activity')]
        self.filters['user_status_activity'].field.choices = tuple(activity_choices)

        activity_choices = [(status.id, status.name) for status in UserStatus.objects.filter(type='filial')]
        self.filters['user_status_filial'].field.choices = tuple(activity_choices)

    class Meta:
        model = UserProfile
        fields = ['courses', 'groups', 'user_status_filial', 'user_status_activity']


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


def user_profile_log_save_to_log_post_save(sender, instance, created, **kwargs):
    user_profile_log = UserProfileLog()
    user_profile_log_dict = copy.deepcopy(instance.__dict__)
    user_profile_log_dict['id'] = None
    user_profile_log.__dict__ = user_profile_log_dict
    user_profile_log.save()
    user_profile_log.user_status.add(*instance.user_status.all())


post_save.connect(create_user_profile, sender=User)
post_save.connect(user_profile_log_save_to_log_post_save, sender=UserProfile)
