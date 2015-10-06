from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def index_message():
    return getattr(settings, 'INDEX_MESSAGE', '')

@register.simple_tag
def all_pages_message():
    return getattr(settings, 'ALL_PAGES_MESSAGE', '')
