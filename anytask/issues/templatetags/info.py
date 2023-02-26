from django import template
from issues.models import Issue
from tasks.models import Task
from command_tasks.models import CommandTask

register = template.Library()


@register.filter(name='get_title_breadcrumb')
def get_issue_task_title(issue, lang):
    if isinstance(issue, Issue):
        if issue.task:
            return u'Issue: {0} {1}'.format(issue.id, issue.task.get_title(lang))
        else:
            return u'Issue: {0} {1}'.format(issue.id, issue.command_task.get_title(lang))


@register.simple_tag
def get_text_from_json(obj, method_name, *args):
    print obj
    if obj:
        method = getattr(obj, method_name)
        return method(*args)
    return ''


@register.filter
def get_title(task, lang):
    if isinstance(task, Task) or isinstance(task, CommandTask):
        return task.get_title(lang)


@register.filter
def get_description(task, lang):
    if isinstance(task, Task) or isinstance(task, CommandTask):
        return task.get_description(lang)
