# -*- coding: utf-8 -*-

from django.contrib import admin

from permissions.models import PermissionsVisible, RolesVisible

class PermissionsVisibleAdmin(admin.ModelAdmin):
    filter_horizontal = ('permissions',)

class RolesVisibleAdmin(admin.ModelAdmin):
    filter_horizontal = ('roles',)

admin.site.register(PermissionsVisible, PermissionsVisibleAdmin)
admin.site.register(RolesVisible, RolesVisibleAdmin)
