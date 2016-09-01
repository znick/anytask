from BeautifulSoup import BeautifulSoup, Comment
from django import template
from django.utils.translation import ugettext as _


register = template.Library()

@register.filter(name='key')
def task_taken_score(d, key):
    return d.get(key)


@register.filter(name='get_name')
def task_taken_score(d, key):
    return d.get(key).last_name + ' ' + d.get(key).first_name


@register.filter(name='get_url')
def task_taken_score(d, key):
    return d.get(key).get_absolute_url()

