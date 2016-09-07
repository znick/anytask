from django import template


register = template.Library()


@register.filter(name='exist')
def another_table_exist(d, index):
    return bool(d[int(not index)])


@register.filter(name='has_item')
def another_table_exist(d, item):
    for x, y in d:
        if x == item:
            return True
    return False
