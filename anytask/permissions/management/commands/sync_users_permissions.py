# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Q

from permissions.models import UserPermissionToUsers
from users.models import UserProfile, UserProfileUserObjectPermission

import time
import logging

logger = logging.getLogger('django.request')


class Command(BaseCommand):
    help = "Sync users permission by UserPermissionToUsers"

    def handle(self, **options):
        start_time = time.time()

        for user_perm_to_users in UserPermissionToUsers.objects.all() \
                .select_related("user__id", "permission__id", "role_from__id"):
            users_profile = UserProfile.objects.filter(
                Q(user__id__in=user_perm_to_users.users.all()) |
                Q(user__group__in=user_perm_to_users.groups.all()) |
                Q(user__group__course__in=user_perm_to_users.courses.all()) |
                Q(user_status__in=user_perm_to_users.statuses.all())
            ).distinct()

            user_perms = UserProfileUserObjectPermission.objects.filter(
                user=user_perm_to_users.user,
                permission=user_perm_to_users.permission,
                role_from=user_perm_to_users.role_from
            )
            user_perms.exclude(content_object__in=users_profile).delete()
            bulk_create_list = []
            for user_profile in users_profile.extra(where=[
                'NOT (users_userprofile.id IN '
                '(SELECT U1.content_object_id FROM users_userprofileuserobjectpermission U1 '
                'WHERE (U1.permission_id = {0} AND U1.user_id = {1} AND U1.content_object_id IS NOT NULL)))'
                        .format(user_perm_to_users.permission.id, user_perm_to_users.user.id)
            ]):
                bulk_create_list.append(
                    UserProfileUserObjectPermission(
                        user=user_perm_to_users.user,
                        permission=user_perm_to_users.permission,
                        role_from=user_perm_to_users.role_from,
                        content_object=user_profile,
                    )
                )

            UserProfileUserObjectPermission.objects.bulk_create(bulk_create_list)

        logger.info("Command sync_users_permissions took %s seconds", time.time() - start_time)
