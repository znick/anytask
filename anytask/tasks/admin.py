from tasks.models import Task, TaskTaken, TaskTakenLog, TaskLog
from django.contrib import admin

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'group', 'weight', 'parent_task', 'score_max')
    list_filter = ('group', 'course', 'course__year__start_year')
    search_fields = ('title', 'course__name', 'group__name', 'task_text')

class TaskLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'group', 'weight', 'parent_task', 'score_max', 'added_time', 'update_time')
    list_filter = ('group', 'course', 'course__year__start_year')
    search_fields = ('title', 'course__name', 'group__name', 'task_text')

class TaskTakenAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'status', 'score', 'scored_by', 'added_time', 'update_time')
    list_filter = ('task__course', 'task__course__year__start_year')

class TaskTakenLogAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'status', 'score', 'scored_by', 'added_time', 'update_time')
    list_filter = ('task__course', 'task__course__year__start_year')

admin.site.register(Task, TaskAdmin)
admin.site.register(TaskLog, TaskLogAdmin)
admin.site.register(TaskTaken, TaskTakenAdmin)
admin.site.register(TaskTakenLog, TaskTakenLogAdmin)
