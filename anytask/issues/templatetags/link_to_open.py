from django import template
from django.conf import settings

register = template.Library()


@register.filter
def is_ipynb(path):
    return path.endswith('.ipynb')

@register.simple_tag
def link_to_open(path, teacher_or_staff):
    if is_ipynb(path) and teacher_or_staff:
        return settings.IPYTHON_URL + path
    return path
