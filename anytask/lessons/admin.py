# coding: utf-8

from lessons.models import Lesson
from django.contrib import admin


class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'group', 'date_starttime', 'date_endtime')
    list_filter = ('group', 'course', 'course__year__start_year')
    search_fields = ('title', 'course__name', 'description')


admin.site.register(Lesson, LessonAdmin)
