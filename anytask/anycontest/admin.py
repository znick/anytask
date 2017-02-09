# -*- coding: utf-8 -*-

from django.contrib import admin

from anycontest.models import ContestSubmission


class ContestSubmissionAdmin(admin.ModelAdmin):
    list_display = ('issue', 'run_id', 'author')
    readonly_fields = ('issue', 'file', 'create_time', 'update_time')
    search_fields = ('issue__id', 'run_id')

admin.site.register(ContestSubmission, ContestSubmissionAdmin)
