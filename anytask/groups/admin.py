from groups.models import Group
from django.contrib import admin


class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'year',)
    list_filter = ('year__start_year',)
    raw_id_fields = ('students', )
    search_fields = ('name', 'year__start_year', 'students__username')


admin.site.register(Group, GroupAdmin)
