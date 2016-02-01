from schools.models import School
from django.contrib import admin

class School(admin.ModelAdmin):
    filter_horizontal = ('courses')
    list_display = ('name')
    list_filter = ('name')
    search_fields = ('name', 'courses_name')


admin.site.register(School, SchoolAdmin)

