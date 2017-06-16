# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User, Permission
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.db.models.loading import get_model

from datetime import datetime
from collections import defaultdict

from years.common import get_current_year
from groups.models import Group
from courses.models import Course
from mail.models import Message
from users.model_user_status import UserStatus

from anytask.storage import OverwriteStorage

from permissions.common import _get_perm_local_name, PERMS_CLASSES, assign_perm_by_id, remove_perm_additional_changes
from permissions.models import PermissionBase, PermissionsVisible, UserPermissionToUsers
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase

import os
import django_filters
import copy

import logging

logger = logging.getLogger('django.request')


def get_upload_path(instance, filename):
    return os.path.join('images', 'user_%d' % instance.user.id, filename)


class UserProfile(models.Model):
    user = models.ForeignKey(User, db_index=True, null=False, blank=False, unique=True, related_name='profile')
    middle_name = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    user_status = models.ManyToManyField(UserStatus, db_index=True, null=True, blank=True,
                                         related_name='users_by_status')

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

    language = models.CharField(default="ru", max_length=128, unique=False, null=True, blank=True)

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

    def add_role(self, role, perms=None, school=None):
        for perm in role.permissions.all():
            perm_objs = perms.get(perm.id, [])
            if not perm_objs:
                perm_objs = perms.get(str(perm.id), [])

            if perm_objs:
                if isinstance(perm_objs, list):
                    for obj_id in perm_objs:
                        model = perm.content_type.model_class()
                        try:
                            obj = model.objects.get(id=obj_id)
                        except model.DoesNotExist:
                            raise PermissionDenied

                        assign_perm_by_id(perm, self.user, obj, role)
                elif isinstance(perm_objs, dict):
                    user_perm_to_users, created = UserPermissionToUsers.objects.get_or_create(
                        user=self.user,
                        permission=perm,
                        role_from=role
                    )
                    user_perm_to_users.users = perm_objs.get('users', [])
                    user_perm_to_users.groups = perm_objs.get('groups', [])
                    user_perm_to_users.courses = perm_objs.get('courses', [])
                    user_perm_to_users.statuses = perm_objs.get('statuses', [])
                else:
                    raise Exception('Unknown perm objects')
            else:
                self.user.user_permissions.add(perm)

        if school:
            user_roles, created = self.user.userroles_set.get_or_create(school=school)
            user_roles.roles.add(role)
        else:
            for roles_visible in role.rolesvisible_set.all():
                user_roles, created = self.user.userroles_set.get_or_create(school=roles_visible.school)
                user_roles.roles.add(role)

    def remove_role(self, role, school=None):
        deleted_perms = []
        for model_app_label, model_names in PERMS_CLASSES.iteritems():
            for model_name in model_names:
                model_perms = get_model(model_app_label, model_name).objects.filter(user=self.user, role_from=role)
                for model_perm in model_perms:
                    remove_perm_additional_changes(model_perm.permission, self.user, model_perm.content_object)
                deleted_perms += model_perms.values_list("permission__id", flat=True)
                model_perms.delete()

        UserPermissionToUsers.objects.filter(user=self.user, role_from=role).delete()

        global_perms = role.permissions.exclude(id__in=deleted_perms)
        if global_perms:
            self.user.user_permissions.remove(*global_perms)

        user_roles = self.user.userroles_set.filter(school=school)
        if user_roles:
            user_roles[0].roles.remove(role)

    def get_perms_by_role(self, role):
        qs_values_list = [
            "id",
            "content_type__app_label",
            "codename",
            "name",
            "userpermissiontousers__users__id",
            "userpermissiontousers__users__first_name",
            "userpermissiontousers__users__last_name",
            "userpermissiontousers__groups__id",
            "userpermissiontousers__groups__name",
            "userpermissiontousers__courses__id",
            "userpermissiontousers__courses__name",
            "userpermissiontousers__statuses__id",
            "userpermissiontousers__statuses__name",
        ]

        qs_filter = Q(userpermissiontousers__role_from=role, userpermissiontousers__user=self.user)
        user_obj_perm_keys = []
        for perm_classes in PERMS_CLASSES.itervalues():
            for perm_class in perm_classes:
                filter_class = {
                    perm_class + "__user": self.user,
                    perm_class + "__role_from": role,
                }
                qs_filter |= Q(**filter_class)
                qs_values_list += [perm_class + "__content_object"]
                user_obj_perm_keys += [perm_class + "__content_object"]
        perms = {}
        for perm_info in Permission.objects.filter(qs_filter).distinct().values(*qs_values_list):
            if perm_info["id"] not in perms:
                group_local_name, perm_local_name = _get_perm_local_name(
                    perm_info['content_type__app_label'],
                    perm_info['codename'],
                    perm_info['name']
                )
                perms[perm_info["id"]] = {
                    "model": perm_info["content_type__app_label"],
                    "codename": perm_info["codename"],
                    "name": perm_local_name,
                    "model_name": group_local_name,
                    "objects": defaultdict(list)
                }
            if perm_info['userpermissiontousers__users__id']:
                perms[perm_info["id"]]["objects"]["user"].append({
                    "id": perm_info['userpermissiontousers__users__id'],
                    "name": u' '.join([
                        perm_info['userpermissiontousers__users__first_name'],
                        perm_info['userpermissiontousers__users__last_name']
                    ]),
                })
            if perm_info['userpermissiontousers__groups__id']:
                perms[perm_info["id"]]["objects"]["group"].append({
                    "id": perm_info['userpermissiontousers__groups__id'],
                    "name": perm_info['userpermissiontousers__groups__name'],
                })
            if perm_info['userpermissiontousers__courses__id']:
                perms[perm_info["id"]]["objects"]["course"].append({
                    "id": perm_info['userpermissiontousers__courses__id'],
                    "name": perm_info['userpermissiontousers__courses__name'],
                })
            if perm_info['userpermissiontousers__statuses__id']:
                perms[perm_info["id"]]["objects"]["status"].append({
                    "id": perm_info['userpermissiontousers__statuses__id'],
                    "name": perm_info['userpermissiontousers__statuses__name'],
                })
            for key in user_obj_perm_keys:
                if perm_info[key]:
                    perms[perm_info["id"]]["objects"]["objects"].append(perm_info[key])
                    break
        return perms

    class Meta:
        permissions = (
            ('view_backoffice_page', 'View backoffice page'),
            ('parent', 'Parent'),
            ('view_profile', 'View profile'),
            ('view_profile_courses_page', 'View user courses page'),
            ('change_perms_for_null_school_users', 'Change permissions for users without school'),
        )


class UserProfileUserObjectPermission(UserObjectPermissionBase, PermissionBase):
    content_object = models.ForeignKey(UserProfile, on_delete=models.CASCADE)


class UserProfileGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(UserProfile, on_delete=models.CASCADE)


class UserProfileLog(models.Model):
    user = models.ForeignKey(User, db_index=True, null=False, blank=False, related_name='profiles_logs_by_user')
    middle_name = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    user_status = models.ManyToManyField(UserStatus, db_index=True, null=True, blank=True)

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

    unread_messages = models.ManyToManyField(Message, null=True, blank=True, related_name='log_unread_messages')
    deleted_messages = models.ManyToManyField(Message, null=True, blank=True, related_name='log_deleted_messages')
    send_notify_messages = models.ManyToManyField(Message, null=True, blank=True,
                                                  related_name='log_send_notify_messages')

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

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


def user_profile_log_save_to_log_post_save(sender, instance, created, **kwargs):
    user_profile_log = UserProfileLog()
    user_profile_log_dict = copy.deepcopy(instance.__dict__)
    user_profile_log_dict['id'] = None
    user_profile_log.__dict__ = user_profile_log_dict
    user_profile_log.save()
    user_profile_log.user_status.add(*instance.user_status.all())
    user_profile_log.unread_messages.add(*instance.unread_messages.all())
    user_profile_log.deleted_messages.add(*instance.deleted_messages.all())
    user_profile_log.send_notify_messages.add(*instance.send_notify_messages.all())


post_save.connect(create_user_profile, sender=User)
post_save.connect(user_profile_log_save_to_log_post_save, sender=UserProfile)
