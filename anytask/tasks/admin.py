from tasks.models import Task, TaskTaken, TaskTakenLog, TaskLog
from django.contrib import admin

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'cource', 'group', 'weight', 'parent_task', 'score_max')
    list_filter = ('group', 'cource', 'cource__year__start_year')
    search_fields = ('title', 'cource__name', 'group__name', 'task_text')

class TaskLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'cource', 'group', 'weight', 'parent_task', 'score_max', 'added_time', 'update_time')
    list_filter = ('group', 'cource', 'cource__year__start_year')
    search_fields = ('title', 'cource__name', 'group__name', 'task_text')

class TaskTakenAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'status', 'score', 'scored_by', 'added_time', 'update_time')
    list_filter = ('task__cource', 'task__cource__year__start_year')

class TaskTakenLogAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'status', 'score', 'scored_by', 'added_time', 'update_time')
    list_filter = ('task__cource', 'task__cource__year__start_year')

admin.site.register(Task, TaskAdmin)
admin.site.register(TaskLog, TaskLogAdmin)
admin.site.register(TaskTaken, TaskTakenAdmin)
admin.site.register(TaskTakenLog, TaskTakenLogAdmin)
