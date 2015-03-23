from users.models import UserProfile
from django.contrib import admin

admin.site.register(UserProfile)

from django.contrib.auth import admin as auth_admin
auth_admin.UserAdmin.list_display += ('last_login',)
