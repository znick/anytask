from BeautifulSoup import BeautifulSoup, Comment
from django import template
from django.utils.translation import ugettext as _
from issues.models import Issue
from issues.model_issue_field import IssueStatusField


register = template.Library()


@register.filter(name='field_in_data')
def form_selected_value(data, field):
    print data
    return data.getlist(field.name)


@register.filter(name='selected')
def form_selected_value(data, val):
    if str(val) in data:
        return 'selected'
    return ''
