# -*- coding: utf-8 -*-

from django.db import models

from django.contrib.auth.models import Permission, Group as Role, User


class PermissionsVisible(models.Model):
    permission = models.ForeignKey(Permission, related_name="permissionsgroup_key", null=True, blank=False)
    school = models.ForeignKey('schools.School', null=True, blank=False)

    permissions = models.ManyToManyField(Permission, related_name='permissionsgroup_set', blank=True)

    def __unicode__(self):
        return u' | '.join((unicode(self.school), unicode(self.permission)))

    class Meta:
        unique_together = (("permission", "school"),)


class RolesVisible(models.Model):
    school = models.ForeignKey('schools.School', null=True, blank=False, unique=True)
    roles = models.ManyToManyField(Role, blank=True)

    def __unicode__(self):
        return unicode(self.school)


class UserRoles(models.Model):
    user = models.ForeignKey(User, db_index=True, null=False, blank=False)
    school = models.ForeignKey('schools.School', null=True, blank=False)
    roles = models.ManyToManyField(Role, blank=True)

    def __unicode__(self):
        return u' | '.join([unicode(self.user), unicode(self.school)])

    class Meta:
        unique_together = (("user", "school"),)


class UserPermissionToUsers(models.Model):
    user = models.ForeignKey(User, db_index=True, null=False, blank=False)
    permission = models.ForeignKey(Permission, null=True, blank=False)
    role_from = models.ForeignKey(Role, null=False, blank=False)

    users = models.ManyToManyField(User, db_index=False, null=True, blank=True,
                                   related_name='user_permission_to_users_by_users')
    groups = models.ManyToManyField('groups.Group', db_index=False, null=True, blank=True)
    courses = models.ManyToManyField('courses.Course', db_index=False, null=True, blank=True)
    statuses = models.ManyToManyField('users.UserStatus', db_index=False, null=True, blank=True)

    def change_by_obj(self, obj, is_added):
        if obj["type"] == "user":
            field = self.users
        elif obj["type"] == "group":
            field = self.groups
        elif obj["type"] == "course":
            field = self.courses
        elif obj["type"] == "status":
            field = self.statuses
        else:
            raise Exception('Unknown object type')

        if is_added:
            field.add(obj["id"])
        else:
            field.remove(obj["id"])

    class Meta:
        unique_together = (("user", "permission", "role_from"),)


class PermissionBase(models.Model):
    role_from = models.ForeignKey(Role, null=True, blank=False)

    class Meta:
        abstract = True
