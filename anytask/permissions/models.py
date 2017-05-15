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


class PermissionBase(models.Model):
    role_from = models.ForeignKey(Role, null=True, blank=False)

    class Meta:
        abstract = True
