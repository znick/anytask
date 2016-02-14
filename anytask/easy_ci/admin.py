from django.contrib import admin

from easy_ci.models import EasyCiTask, EasyCiCheck

class EasyCiTaskAdmin(admin.ModelAdmin):
    list_display = ('student', 'task', 'added_time', 'update_time')
    list_filter = ("task__cource", "task__cource__year", "student__group")
    search_fields = ('student', 'task', 'data')

admin.site.register(EasyCiTask, EasyCiTaskAdmin)

class EasyCiCheckAdmin(admin.ModelAdmin):
    list_display = ('easy_ci_task', 'exit_status')

admin.site.register(EasyCiCheck, EasyCiCheckAdmin)
