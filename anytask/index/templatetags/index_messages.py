from django import template
from django.conf import settings
from django.utils.html import mark_safe

register = template.Library()


@register.simple_tag
def index_message():
    return mark_safe(getattr(settings, 'INDEX_MESSAGE', ''))


@register.simple_tag
def all_pages_message():
    return mark_safe(getattr(settings, 'ALL_PAGES_MESSAGE', ''))
