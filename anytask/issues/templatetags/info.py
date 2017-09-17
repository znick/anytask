from django import template
from issues.models import Issue
from tasks.models import Task

register = template.Library()


@register.filter(name='get_title_breadcrumb')
def get_issue_task_title(issue, lang):
    if isinstance(issue, Issue):
        return u'Issue: {0} {1}'.format(issue.id, issue.task.get_title(lang))


@register.simple_tag
def get_text_from_json(obj, method_name, *args):
    method = getattr(obj, method_name)
    return method(*args)


@register.filter
def get_title(task, lang):
    if isinstance(task, Task):
        return task.get_title(lang)


@register.filter
def get_description(task, lang):
    if isinstance(task, Task):
        return task.get_description(lang)
