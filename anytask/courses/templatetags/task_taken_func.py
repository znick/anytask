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


@register.filter(name='group_info')
def task_group_info(task):
    if isinstance(task, Task):
        data_task_groups = set()
        data_task_disabled_groups = set()
        data_task_empty_children_groups = set()

        for group in task.groups.all():
            data_task_groups.add(str(group.id))
            if task.type == 'Seminar':
                if task.children.count():
                    for child in task.children.all():
                        if Issue.objects.filter(task=child, student__in=group.students.all()).count():
                            data_task_disabled_groups.add(str(group.id))
                        elif group in child.groups.all():
                            data_task_empty_children_groups.add(str(group.id))

            elif Issue.objects.filter(task=task, student__in=group.students.all()).count():
                data_task_disabled_groups.add(str(group.id))

        return " data-task_groups = '[{0}]' data-task_disabled_groups = '[{1}]'  data-task_empty_children_groups = '[{2}]'" \
            .format(', '.join(data_task_groups),
                    ', '.join(data_task_disabled_groups),
                    ', '.join(data_task_empty_children_groups))
    return ''
