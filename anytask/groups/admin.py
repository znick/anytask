from groups.models import Group
from django.contrib import admin


class GroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('students',)
    list_display = ('name', 'year',)
    list_filter = ('name', 'year__start_year',)
    search_fields = ('name', 'year__start_year', 'students__username')


admin.site.register(Group, GroupAdmin)
