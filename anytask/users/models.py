# -*- coding: utf-8 -*-

import logging
import os

from courses.models import Course
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from groups.models import Group
from mail.models import Message
from users.model_user_status import UserStatus
from years.common import get_current_year

from anytask.storage import OverwriteStorage

logger = logging.getLogger('django.request')


def get_upload_path(instance, filename):
    return os.path.join('images', 'user_%d' % instance.user.id, filename)


class UserProfile(models.Model):
    user = models.OneToOneField(User, db_index=True, null=False, blank=False, unique=True, related_name='profile')
    middle_name = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    user_status = models.ManyToManyField(UserStatus, db_index=True, blank=True, related_name='users_by_status')

    avatar = models.ImageField('profile picture', upload_to=get_upload_path, blank=True, null=True,
                               storage=OverwriteStorage())
    birth_date = models.DateField(blank=True, null=True)

    info = models.TextField(default="", blank=True, null=True)

    phone = models.CharField(max_length=128, null=True, blank=True)
    city_of_residence = models.CharField(max_length=191, null=True, blank=True)

    university = models.CharField(max_length=191, null=True, blank=True)
    university_in_process = models.BooleanField(null=False, blank=False, default=False)
    university_class = models.CharField(max_length=191, null=True, blank=True)
    university_department = models.CharField(max_length=191, null=True, blank=True)
    university_year_end = models.CharField(max_length=191, null=True, blank=True)

    additional_info = models.TextField(null=True, blank=True)

    unit = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    position = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    academic_degree = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    academic_title = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    show_email = models.BooleanField(db_index=False, null=False, blank=False, default=True)
    send_my_own_events = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    unread_messages = models.ManyToManyField(Message, blank=True, related_name='unread_messages')
    deleted_messages = models.ManyToManyField(Message, blank=True, related_name='deleted_messages')
    send_notify_messages = models.ManyToManyField(Message, blank=True, related_name='send_notify_messages')

    added_time = models.DateTimeField(auto_now_add=True)  # remove default=timezone.now
    update_time = models.DateTimeField(auto_now=True)  # remove default=timezone.now

    updated_by = models.ForeignKey(User, db_index=False, null=True, blank=True)

    login_via_yandex = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    ya_uid = models.IntegerField(null=True, blank=True)
    ya_login = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    ya_contest_uid = models.CharField(max_length=191, null=True, blank=True)
    ya_contest_oauth = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    ya_contest_login = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    ya_passport_uid = models.CharField(max_length=191, null=True, blank=True)
    ya_passport_oauth = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    ya_passport_login = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    ya_passport_email = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    language = models.CharField(default="ru", max_length=128, unique=False, null=True, blank=True)
    time_zone = models.TextField(null=False, blank=False, default='Europe/Moscow')
    location = models.TextField(null=True, blank=True, default="")

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
    middle_name = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    user_status = models.ManyToManyField(UserStatus, db_index=True, blank=True)

    avatar = models.ImageField('profile picture', upload_to=get_upload_path, blank=True, null=True,
                               storage=OverwriteStorage())
    birth_date = models.DateField(blank=True, null=True)

    info = models.TextField(default="", blank=True, null=True)

    phone = models.CharField(max_length=128, null=True, blank=True)
    city_of_residence = models.CharField(max_length=191, null=True, blank=True)

    university = models.CharField(max_length=191, null=True, blank=True)
    university_in_process = models.BooleanField(null=False, blank=False, default=False)
    university_class = models.CharField(max_length=50, null=True, blank=True)
    university_department = models.CharField(max_length=191, null=True, blank=True)
    university_year_end = models.CharField(max_length=20, null=True, blank=True)

    additional_info = models.TextField(null=True, blank=True)

    unit = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    position = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    academic_degree = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)
    academic_title = models.CharField(default="", max_length=128, unique=False, null=True, blank=True)

    show_email = models.BooleanField(db_index=False, null=False, blank=False, default=True)
    send_my_own_events = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    unread_messages = models.ManyToManyField(Message, blank=True, related_name='log_unread_messages')
    deleted_messages = models.ManyToManyField(Message, blank=True, related_name='log_deleted_messages')
    send_notify_messages = models.ManyToManyField(Message, blank=True, related_name='log_send_notify_messages')

    added_time = models.DateTimeField(auto_now_add=True)  # remove default=timezone.now
    update_time = models.DateTimeField(auto_now=True)  # remove default=timezone.now

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

    language = models.CharField(default="ru", max_length=128, unique=False, null=True, blank=True)

    updated_by = models.ForeignKey(User, db_index=False, null=True, blank=True)

    def is_current_year_student(self):
        return Group.objects.filter(year=get_current_year()).filter(students=self.user).count() > 0

    def __unicode__(self):
        return unicode(self.user)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User)
