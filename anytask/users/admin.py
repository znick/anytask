# -*- coding: utf-8 -*-

from users.models import UserProfile
from users.model_user_status import UserStatus
from django.contrib import admin
from django.utils.translation import ugettext as _
from django.contrib.auth import admin as auth_admin

from reversion.admin import VersionAdmin


def display_color(obj):
    return u'<span style="' \
           u'padding: .25em .4em;' \
           u'font-size: 75%;' \
           u'font-weight: 700;' \
           u'line-height: 1;' \
           u'color: #000;' \
           u'text-align: center;' \
           u'white-space: nowrap;' \
           u'vertical-align: baseline;' \
           u'border-radius: .25rem;' \
           u'background-color:{0}' \
           u'">{1}</span>'.format(obj.color, obj.name)


display_color.short_description = _(u'status')
display_color.allow_tags = True


class UserStatusAdmin(admin.ModelAdmin):
    list_display = (display_color, 'tag', 'type')
    search_fields = ('name',)

    def queryset(self, request):
        qs = super(UserStatusAdmin, self).queryset(request)
        # if request.user.is_superuser:
        #     return qs
        return qs


class UserProfileBaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'update_time')
    filter_horizontal = ('user_status',)
    raw_id_fields = ('unread_messages', 'deleted_messages', 'send_notify_messages')
    search_fields = ('user__username', 'user_status__name')


class UserProfileAdmin(VersionAdmin, UserProfileBaseAdmin):
    pass


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserStatus, UserStatusAdmin)

auth_admin.UserAdmin.list_display = (
    'id', 'username', 'email', 'first_name', 'last_name',
    'is_active', 'is_staff', 'is_superuser', 'last_login'
)
auth_admin.UserAdmin.search_fields += ('id',)
