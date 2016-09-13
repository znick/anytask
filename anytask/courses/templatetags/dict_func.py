from BeautifulSoup import BeautifulSoup, Comment
from django import template
from django.utils.translation import ugettext as _


register = template.Library()


@register.filter(name='key')
def get_key(d, key):
    return d.get(key)


@register.filter(name='get_name')
def get_full_name(d, key):
    return d.get(key).last_name + ' ' + d.get(key).first_name


@register.filter(name='get_url')
def get_url(d, key):
    return d.get(key).get_absolute_url()

