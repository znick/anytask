from BeautifulSoup import BeautifulSoup, Comment
from django import template
from django.utils.translation import ugettext as _
from issues.models import Issue
from issues.model_issue_status import IssueStatus
from tasks.models import Task

register = template.Library()


@register.filter(name='score')
def task_taken_score(d, task):
    if d.has_key(task.id):
        if isinstance(d[task.id], Issue):
            return d[task.id].score()
        else:
            return d[task.id].score
    return 0


@register.filter(name='comment')
def task_taken_comment(d, task):
    if d.has_key(task.id):
        if isinstance(d[task.id], Issue):
            return d[task.id].last_comment()
        else:
            return d[task.id].teacher_comments
    return ''


@register.filter(name='have_issue')
def issue_have_issue(d, task):
    if d.has_key(task.id):
        return ''
    return 'no-issue'


@register.filter(name='label_color')
def issue_label_color(d, task):
    if d.has_key(task.id):
        if isinstance(d[task.id], Issue):
            return d[task.id].status_field.color
    return IssueStatus.COLOR_DEFAULT


@register.filter(name='can_be_deleted')
def task_can_be_deleted(task):
    if isinstance(task, Task):
        if Issue.objects.filter(task=task).count():
            return False
        else:
            return True
    return False
