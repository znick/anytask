# coding: utf-8

from lessons.models import Lesson
from django.contrib import admin


class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'group', 'date_starttime', 'date_endtime')
    list_filter = ('group', 'course', 'course__year__start_year')
    search_fields = ('title', 'course__name', 'description')

#
# class LessonGroupRelationsAdmin(admin.ModelAdmin):
#     list_display = ('lesson', 'group', 'position', 'deleted')
#     list_filter = ('lesson__course', 'group')
#     search_fields = ('lesson__title', 'lesson__course__name', 'group__name', 'lesson__task_text')


admin.site.register(Lesson, LessonAdmin)
# admin.site.register(LessonGroupRelations, LessonGroupRelationsAdmin)
