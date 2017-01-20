from django import template
from issues.models import Issue
from issues.model_issue_status import IssueStatus

register = template.Library()


@register.filter(name='get_score')
def get_score(task, user):
    try:
        return Issue.objects.get(task=task, student=user).mark
    except Exception as e:
        return 0


@register.filter(name='get_status_label')
def get_status_label(task, user):
    try:
        return Issue.objects.get(task=task, student=user).status_field.color
    except Exception as e:
        return IssueStatus.COLOR_DEFAULT
