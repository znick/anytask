from courses.models import Course, FilenameExtension, DefaultTeacher, MarkField, CourseMarkSystem, StudentCourseMark
from django.contrib import admin


class CourseAdmin(admin.ModelAdmin):
    filter_horizontal = ('teachers', 'groups', 'filename_extensions', 'issue_fields')
    list_display = ('name', 'year',)
    list_filter = ('name', 'year__start_year', 'is_active')
    search_fields = ('name', 'year__start_year', 'teachers__username', 'groups__name')


class DefaultTeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'group', 'course')
    list_filter = ('group', 'course')


class CourseMarkSystemAdmin(admin.ModelAdmin):
    filter_horizontal = ('marks',)


class StudentCourseMarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'mark')
    list_filter = ('student', 'course', 'mark')
    readonly_fields = ('update_time',)


class MarkFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_int')


admin.site.register(Course, CourseAdmin)
admin.site.register(FilenameExtension)
admin.site.register(DefaultTeacher, DefaultTeacherAdmin)
admin.site.register(CourseMarkSystem, CourseMarkSystemAdmin)
admin.site.register(MarkField, MarkFieldAdmin)
admin.site.register(StudentCourseMark, StudentCourseMarkAdmin)
