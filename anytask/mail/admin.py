# -*- coding: utf-8 -*-

from mail.models import Message
from django.contrib import admin


class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'title')
    filter_horizontal = ('recipients', 'recipients_user', 'recipients_group', 'recipients_course', 'recipients_status')


admin.site.register(Message, MessageAdmin)
