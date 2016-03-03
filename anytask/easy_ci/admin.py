from django.contrib import admin

from easy_ci.models import EasyCiTask, EasyCiCheck


def set_unchecked(modeladmin, request, queryset):
    queryset.update(checked=False)
set_unchecked.short_description = "Mark tasks unchecked"

class EasyCiTaskAdmin(admin.ModelAdmin):
    list_display = ('student', 'task', 'added_time', 'update_time')
    list_filter = ("task__cource", "task__cource__year", "student__group")
    search_fields = ('student', 'task', 'data')
    actions = [set_unchecked]


admin.site.register(EasyCiTask, EasyCiTaskAdmin)

class EasyCiCheckAdmin(admin.ModelAdmin):
    list_display = ('easy_ci_task', 'exit_status')
    list_filter = ("easy_ci_task__task", "easy_ci_task__task__cource__year", "easy_ci_task__student__group", "type")

admin.site.register(EasyCiCheck, EasyCiCheckAdmin)
