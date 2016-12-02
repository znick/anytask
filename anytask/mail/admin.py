# -*- coding: utf-8 -*-

from mail.models import Message
from django.contrib import admin


class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender',  'title')
    filter_horizontal = ('recipients',)


admin.site.register(Message, MessageAdmin)
