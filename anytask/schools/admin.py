from schools.models import School
from django.contrib import admin

from guardian.admin import GuardedModelAdmin


class SchoolAdmin(GuardedModelAdmin):
    filter_horizontal = ('courses',)
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name', 'courses_name',)


admin.site.register(School, SchoolAdmin)
