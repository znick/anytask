from courses.models import Course, FilenameExtension
from django.contrib import admin

class CourseAdmin(admin.ModelAdmin):
    filter_horizontal = ('students', 'teachers', 'groups', 'filename_extensions', 'issue_fields')
    list_display = ('name', 'year', )
    list_filter = ('name', 'year__start_year', 'is_active')
    search_fields = ('name', 'year__start_year', 'students__username', 'teachers__username', 'groups__name', 'filename_extensions_name')

admin.site.register(Course, CourseAdmin)
admin.site.register(FilenameExtension)
