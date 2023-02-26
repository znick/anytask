from django import template
from issues.models import Issue

register = template.Library()


def convert_status_to_icon(task_taken):
    if task_taken is None:
        return ""
    if isinstance(task_taken, Issue):
        return ''

    if task_taken.status_check == task_taken.EDIT:
        return "icon-wrench"
    elif task_taken.status_check == task_taken.QUEUE:
        return "icon-question-sign"
    elif task_taken.status_check == task_taken.OK:
        return "icon-ok-sign"
    else:
        return ""


def check_in_queue(task_taken):
    if task_taken is None:
        return False

    return task_taken.status_check == task_taken.QUEUE


def get_task_taken(task_taken_set, task):
    if task.id in task_taken_set:
        task = task_taken_set[task.id]
        return task
    else:
        return None


def get_color_label_in_queue_to_check(task_taken, color_set):
    if task_taken is None:
        return ""
    if task_taken.teacher is None:
        return "grey"
    elif task_taken.teacher.id in color_set:
        return color_set[task_taken.teacher.id][0]
    else:
        return "label-info"


def get_teacher(task_taken):
    if task_taken.teacher is None:
        return "None"
    else:
        return task_taken.teacher.username


register.filter('icon', convert_status_to_icon)
register.filter('in_queue', check_in_queue)
register.filter('get_teacher', get_teacher)
register.filter('get_task_taken', get_task_taken)
register.filter('color_label_in_teacher_queue', get_color_label_in_queue_to_check)
