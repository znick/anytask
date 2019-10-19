from tasks.models import Task, TaskTaken, TaskLog, TaskGroupRelations
from django.contrib import admin
import reversion


class TaskBaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'get_groups', 'weight', 'parent_task', 'score_max')
    list_filter = ('groups', 'course', 'course__year__start_year')
    search_fields = ('title', 'course__name', 'task_text')
    filter_horizontal = ('groups', )

    def get_groups(self, obj):
        return "; ".join([group.name for group in obj.groups.all()])

    get_groups.short_description = 'Groups'


class TaskAdmin(reversion.VersionAdmin, TaskBaseAdmin):
    pass


class TaskLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'get_groups', 'weight', 'parent_task', 'score_max', 'added_time', 'update_time')
    list_filter = ('groups', 'course', 'course__year__start_year')
    search_fields = ('title', 'course__name', 'task_text')

    def get_groups(self, obj):
        return "; ".join([group.name for group in obj.groups.all()])

    get_groups.short_description = 'Groups'


class TaskTakenAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'status', 'taken_time', 'blacklisted_till', 'added_time', 'update_time')
    list_filter = ('task__course', 'task__course__year__start_year')
    readonly_fields = ('score',)


class TaskGroupRelationsAdmin(admin.ModelAdmin):
    list_display = ('task', 'group', 'position', 'deleted')
    list_filter = ('task__course', 'group')
    search_fields = ('task__title', 'task__course__name', 'group__name', 'task__task_text')


admin.site.register(Task, TaskAdmin)
admin.site.register(TaskLog, TaskLogAdmin)
admin.site.register(TaskTaken, TaskTakenAdmin)
admin.site.register(TaskGroupRelations, TaskGroupRelationsAdmin)
