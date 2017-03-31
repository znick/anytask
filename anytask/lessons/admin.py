# coding: utf-8

from lessons.models import Lesson, LessonGroupRelations
from django.contrib import admin


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


admin.site.register(Lesson, LessonAdmin)
admin.site.register(LessonGroupRelations, LessonGroupRelationsAdmin)
