# -*- coding: utf-8 -*-
from django import template
from django.utils.translation import ugettext as _
from issues.models import Issue
from issues.model_issue_status import IssueStatus
from groups.models import Group
from courses.models import Course, DefaultTeacher

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
        return _(u"novyj")


@register.filter(name='get_default_teacher')
def get_default_teacher(group, course):
    try:
        return DefaultTeacher.objects.get(group=group, course=course).teacher.get_full_name()
    except Exception as e:
        return ""
