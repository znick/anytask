from django import template
from issues.models import Issue


register = template.Library()


@register.filter(name='exist')
def another_table_exist(d, index):
    return bool(d[int(not index)])


@register.filter(name='has_item')
def item_in_tuple(d, item):
    for x, y in d:
        if x == item:
            return True
    return False


@register.filter(name='get_status')
def status_get_name(issue, lang):
    if isinstance(issue, Issue):
        return issue.status_field.get_name(lang)
