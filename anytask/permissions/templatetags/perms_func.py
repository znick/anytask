# -*- coding: utf-8 -*-

from django import template
from guardian.shortcuts import get_objects_for_user

register = template.Library()


@register.filter(name='has_any_obj_permission')
def has_any_obj_permission(user, perm):
    if get_objects_for_user(user, perm).count():
        return True
    return False
