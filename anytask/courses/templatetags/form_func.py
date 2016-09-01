from BeautifulSoup import BeautifulSoup, Comment
from django import template
from django.http import QueryDict


register = template.Library()


@register.filter(name='field_in_data')
def form_selected_value(data, field):
    if isinstance(data, QueryDict):
        return data.getlist(field.name)
    return []


@register.filter(name='selected')
def form_selected_value(data, val):
    if str(val) in data:
        return 'selected'
    return ''
