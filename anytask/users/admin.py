from users.models import UserProfile
from django.contrib import admin


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)

admin.site.register(UserProfile, UserProfileAdmin)

from django.contrib.auth import admin as auth_admin
auth_admin.UserAdmin.list_display += ('last_login',)
