from command_tasks.models import CommandTask, CommandTaskTaken, CommandTaskLog, CommandTaskGroupRelations
from django.contrib import admin
from reversion.admin import VersionAdmin


class CommandTaskBaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'get_groups', 'weight', 'parent_task', 'score_max')
    list_filter = ('groups', 'course', 'course__year__start_year')
    search_fields = ('title', 'course__name', 'task_text')
    filter_horizontal = ('groups', )

    def get_groups(self, obj):
        return "; ".join([group.name for group in obj.groups.all()])

    get_groups.short_description = 'Groups'


class CommandTaskAdmin(VersionAdmin, CommandTaskBaseAdmin):
    pass


class CommandTaskLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'get_groups', 'weight', 'parent_task', 'score_max', 'added_time', 'update_time')
    list_filter = ('groups', 'course', 'course__year__start_year')
    search_fields = ('title', 'course__name', 'task_text')

    def get_groups(self, obj):
        return "; ".join([group.name for group in obj.groups.all()])

    get_groups.short_description = 'Groups'


class CommandTaskTakenAdmin(admin.ModelAdmin):
    list_display = ('task', 'first_user', 'second_user', 'third_user', 'status', 'taken_time', 'blacklisted_till', 'added_time', 'update_time')
    list_filter = ('task__course', 'task__course__year__start_year')
    readonly_fields = ('first_user_score', 'second_user_score', 'third_user_score', 'third_user_enabled',)


class CommandTaskGroupRelationsAdmin(admin.ModelAdmin):
    list_display = ('task', 'group', 'position', 'deleted')
    list_filter = ('task__course', 'group')
    search_fields = ('task__title', 'task__course__name', 'group__name', 'task__task_text')


admin.site.register(CommandTask, CommandTaskAdmin)
admin.site.register(CommandTaskLog, CommandTaskLogAdmin)
admin.site.register(CommandTaskTaken, CommandTaskTakenAdmin)
admin.site.register(CommandTaskGroupRelations, CommandTaskGroupRelationsAdmin)
