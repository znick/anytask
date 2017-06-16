# -*- coding: utf-8 -*-

from django.contrib import admin

from permissions.models import PermissionsVisible, RolesVisible, UserRoles, UserPermissionToUsers

class PermissionsVisibleAdmin(admin.ModelAdmin):
    filter_horizontal = ('permissions',)
    list_display = ('school', 'permission')

class RolesVisibleAdmin(admin.ModelAdmin):
    filter_horizontal = ('roles',)

class UserRolesAdmin(admin.ModelAdmin):
    filter_horizontal = ('roles',)
    list_display = ('user', 'school')
    list_filter = ('school',)
    search_fields = ('user__username', 'user__last_name', 'user__first_name', 'school__name')

class UserPermissionToUsersAdmin(admin.ModelAdmin):
    filter_horizontal = ('users', 'groups', 'courses', 'statuses')
    list_display = ('user', 'permission', 'role_from')

admin.site.register(PermissionsVisible, PermissionsVisibleAdmin)
admin.site.register(RolesVisible, RolesVisibleAdmin)
admin.site.register(UserRoles, UserRolesAdmin)
admin.site.register(UserPermissionToUsers, UserPermissionToUsersAdmin)
