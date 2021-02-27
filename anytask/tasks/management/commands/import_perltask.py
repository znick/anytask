"""
A management command which deletes expired accounts (e.g.,
accounts which signed up but never activated) from the database.

Calls ``RegistrationProfile.objects.delete_expired_users()``, which
contains the actual logic for determining which accounts are deleted.

"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from xml.etree.ElementTree import parse
import sys
import datetime
from optparse import make_option

from years.common import get_or_create_current_year
from years.models import Year
from courses.models import Course
from tasks.models import Task, TaskTaken
from groups.models import Group


def get_task_lines(task):
    for task_line in task.getElementsByTagName("tb")[0].getElementsByTagName("l"):
        line = ''
        for l_child in task_line.childNodes:
            if l_child.nodeType != l_child.TEXT_NODE and l_child.tagName == "i":
                line += l_child.firstChild.data
            else:
                line += l_child.data
        yield line


def get_datetime(cs_date):
    if not cs_date:
        return None
    d, m, y = cs_date.split('.')
    d = int(d)
    m = int(m)
    y = int(y)
    y += 2000

    return datetime.datetime(year=y, month=m, day=d)


def import_tasktakens(task_obj, tasktakens_el, year):
    for s in tasktakens_el.getElementsByTagName('s'):
        last_name, first_name = s.getAttribute('fi').split(' ')
        group_name = s.getAttribute('g')
        added_time = get_datetime(s.getAttribute('d1'))
        update_time = get_datetime(s.getAttribute('d2'))
        score = s.getAttribute('b')

        try:
            user = User.objects.get(first_name=first_name, last_name=last_name)
        except User.MultipleObjectsReturned:
            user_count = User.objects.filter(first_name=first_name, last_name=last_name).count()
            user = User.objects.filter(first_name=first_name, last_name=last_name)[user_count - 1]
            print("WARNING user '{0}' MultipleObjectsReturned, selected: '{1}'".format(
                user.get_full_name().encode("utf-8"), user))

        task_taken, _ = TaskTaken.objects.get_or_create(user=user, task=task_obj)
        group, _ = Group.objects.get_or_create(year=year, name=group_name)
        task_obj.course.groups.add(group)
        group.students.add(user)

        for field in task_taken._meta.local_fields:
            if field.name == "update_time":
                field.auto_now = False

        task_taken.added_time = added_time
        task_taken.update_time = added_time
        task_taken.status = TaskTaken.STATUS_TAKEN
        if score:
            task_taken.status = TaskTaken.STATUS_SCORED
            task_taken.score = score
            task_taken.update_time = update_time
        task_taken.save()

        for field in task_taken._meta.local_fields:
            if field.name == "update_time":
                field.auto_now = True

        print(">>>>{0} {1} {2} {3}".format(user, user.get_full_name().encode("utf-8"), group, score))


def import_task_no_subtasks(task_el, course, year):
    max_score = task_el.getAttribute('b')
    title = task_el.getElementsByTagName('th')[0].firstChild.data.rsplit('[', 1)[0].strip()
    weight = task_el.getAttribute('n')
    print(title)
    text = "\n".join(get_task_lines(task_el))
    task_obj, _ = Task.objects.get_or_create(title=title, course=course, task_text=text, score_max=max_score)
    task_obj.weight = weight
    task_obj.save()
    try:
        import_tasktakens(task_obj, task_el.getElementsByTagName('ts')[0], year)
    except IndexError:  # no task takens
        pass


def import_task_with_subtasks(task_el, course, year):
    title = task_el.getElementsByTagName('th')[0].firstChild.data.rsplit('[', 1)[0]
    weight = task_el.getAttribute('n')
    print(title)
    text = "\n".join(get_task_lines(task_el))
    parent_task, _ = Task.objects.get_or_create(title=title, course=course, task_text=text)
    parent_task.weight = weight
    parent_task.save()
    for subtask_el in task_el.getElementsByTagName('tm')[0].getElementsByTagName('t'):
        title = subtask_el.getAttribute('h').rsplit('[', 1)[0]
        weight = subtask_el.getAttribute('m')
        print(">>" + title)
        max_score = subtask_el.getAttribute('b')
        subtask_obj, _ = Task.objects.get_or_create(title=title, course=course, score_max=max_score,
                                                    parent_task=parent_task)
        subtask_obj.weight = weight
        subtask_obj.save()
        try:
            import_tasktakens(subtask_obj, subtask_el, year)
        except IndexError:  # no task takens
            pass


def import_perltask(perltask_xml, year=None):
    if year is None:
        year = get_or_create_current_year()
    course, created = Course.objects.get_or_create(year=year, name='Perltask')
    if created:
        print("WARNING: NEW Course created!")
        course.type = Course.TYPE_POTOK
        course.take_policy = Course.TAKE_POLICY_SELF_TAKEN
        course.max_users_per_task = 8
        course.max_days_without_score = 30
        course.days_drop_from_blacklist = 14
        course.save()

    doc = parse(perltask_xml)
    for task in doc.getElementsByTagName("task"):
        if task.getAttribute('m'):  # got_substasks
            import_task_with_subtasks(task, course, year)
        else:
            import_task_no_subtasks(task, course, year)


class Command(BaseCommand):
    help = "Import users from cs.usu.edu.ru/home. Put default.xml to STDIN"

    option_list = BaseCommand.option_list + (
        make_option('--year',
                    action='store',
                    dest='year',
                    default=None,
                    help='Course start year'),
    )

    def handle(self, *args, **options):
        year = options['year']
        if year:
            year = int(year)
            year, _ = Year.objects.get_or_create(start_year=year)
        import_perltask(sys.stdin, year=year)
