from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def link_to_open(file, course, user):
    path = file.file.url
    if '.ipynb' in path:
        if course.user_is_teacher(user):
            return settings.IPYTHON_URL + path
        else:
            return path
    else:
        return path
