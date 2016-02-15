from invites.models import Invite
from django.contrib import admin

class InviteAdmin(admin.ModelAdmin):
	filter_horizontal = ('invited_users',)
    list_display = ('generated_by', 'group', 'key')
    list_filter = ('group',)
    search_fields = ('generated_by__username', 'group__name', 'key')

admin.site.register(Invite, InviteAdmin)

