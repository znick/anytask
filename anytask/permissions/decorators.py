# -*- coding: utf-8 -*-

from django.utils.functional import wraps
from guardian.shortcuts import get_objects_for_user
from django.core.exceptions import PermissionDenied


def any_obj_permission_required_or_403(perm):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not get_objects_for_user(request.user, perm).exists():
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wraps(view_func)(_wrapped_view)

    return decorator
