from BeautifulSoup import BeautifulSoup, Comment
from django import template
from django.utils.translation import ugettext as _


register = template.Library()

@register.filter(name='key')
def task_taken_score(d, key):
    return d.get(key)

