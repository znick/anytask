# coding: utf-8

from lessons.models import Lesson, LessonGroupRelations, Schedule
from django.contrib import admin


class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('subject', 'course', 'group', 'period', 'date_start', 'date_end', )
    list_filter = ('group', 'course', 'course__year__start_year')
    search_fields = ('subject', 'course__name', 'lesson_text')


class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'get_groups', 'lesson_date')
    list_filter = ('groups', 'course', 'course__year__start_year')
    search_fields = ('title', 'course__name', 'lesson_text')

    def get_groups(self, obj):
        return "; ".join([group.name for group in obj.groups.all()])
    get_groups.short_description = 'Groups'


class LessonGroupRelationsAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'group', 'position', 'deleted')
    list_filter = ('lesson__course', 'group')
    search_fields = ('lesson__title', 'lesson__course__name', 'group__name', 'lesson__task_text')


admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(LessonGroupRelations, LessonGroupRelationsAdmin)
