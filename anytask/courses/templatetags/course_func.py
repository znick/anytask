from django import template
from issues.models import Issue

register = template.Library()


@register.filter(name='get_score')
def get_score(task, user):
    try:
        return Issue.objects.get(task=task, student=user).mark
    except Exception as e:
        return 0


@register.filter(name='get_status_label')
def get_status_label(d, key):
    return d.get(key).last_name + ' ' + d.get(key).first_name
