# -*- coding: utf-8 -*-
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


@register.filter(name='get_status_color')
def get_status_color(task, user):
    try:
        return Issue.objects.get(task=task, student=user).status_field.color
    except Exception as e:
        return IssueStatus.COLOR_DEFAULT


@register.filter(name='get_status_name')
def get_status_name(task, user):
    try:
        return Issue.objects.get(task=task, student=user).status_field.name
    except Exception as e:
        return u"Новая"
