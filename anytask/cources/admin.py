from cources.models import Cource
from django.contrib import admin

class CourceAdmin(admin.ModelAdmin):
    filter_horizontal = ('students', 'teachers', 'groups')
    list_display = ('name', 'year', )
    list_filter = ('name', 'year__start_year', 'is_active')
    search_fields = ('name', 'year__start_year', 'students__username', 'teachers__username', 'groups__name')

admin.site.register(Cource, CourceAdmin)
