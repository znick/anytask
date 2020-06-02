#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
import datetime
from django.db.models import Q
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from courses.models import Course
from tasks.models import TaskTaken


class Command(BaseCommand):
    help = 'Task taken clenup'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.out_lines = []
        self.need_print = False

    @transaction.atomic()
    def check_course_task_taken_expires(self, course):
        if not settings.PYTHONTASK_MAX_DAYS_WITHOUT_SCORES:
            return

        task_expired_date = datetime.datetime.now() - datetime.timedelta(
            days=settings.PYTHONTASK_MAX_DAYS_WITHOUT_SCORES)
        for task in course.task_set.all():
            task_taken_query = TaskTaken.objects.filter(task=task)
            task_taken_query = task_taken_query.filter(
                Q(Q(status=TaskTaken.STATUS_SCORED, issue__mark=0.0)
                  | Q(status=TaskTaken.STATUS_TAKEN)
                  | Q(status=TaskTaken.STATUS_CANCELLED)))
            task_taken_query = task_taken_query.filter(taken_time__lte=task_expired_date)

            task_taken_to_delete = []
            task_taken_to_blacklist = []
            for task_taken in task_taken_query:
                if (task_taken.status == TaskTaken.STATUS_TAKEN) or \
                   (task_taken.status == TaskTaken.STATUS_SCORED and task_taken.issue.mark == 0.0):

                    self.out_lines.append(">Blacklisting task_taken : {0}".format(task_taken))
                    self.need_print = True
                    task_taken_to_blacklist.append(task_taken)

                if task_taken.status == TaskTaken.STATUS_CANCELLED:
                    self.out_lines.append(">Dropping task_taken : {0}".format(task_taken))
                    self.need_print = True
                    task_taken_to_delete.append(task_taken)

            for task_taken in task_taken_to_blacklist:
                task_taken.blacklist()
                task_taken.issue.add_comment(
                    u"Запись на задачу отменена автоматически в связи с истечением времени сдачи")

            for task_taken in task_taken_to_delete:
                task_taken.mark_deleted()

    @transaction.atomic()
    def check_blacklist_expires(self, course):
        if not settings.PYTHONTASK_DAYS_DROP_FROM_BLACKLIST:
            return

        now = timezone.now()

        for task in course.task_set.all():
            task_taken_query = TaskTaken.objects.filter(task=task)
            task_taken_query = task_taken_query.filter(status=TaskTaken.STATUS_BLACKLISTED)
            task_taken_query = task_taken_query.filter(blacklisted_till__lte=now)

            task_taken_to_delete = []
            for task_taken in task_taken_query:
                self.out_lines.append(">Dropping task_taken : {0}".format(task_taken))
                self.need_print = True
                task_taken_to_delete.append(task_taken)

            for task_taken in task_taken_to_delete:
                task_taken.mark_deleted()
                task_taken.issue.add_comment(u"На задачу снова можно записаться")

    def handle(self, *args, **options):
        for course in Course.objects.filter(is_python_task=True):
            for task in course.task_set.all():
                for task_taken in TaskTaken.objects.filter(task=task):
                    task_taken.update_status()

            self.out_lines.append("Course '{0}'".format(course))
            self.check_course_task_taken_expires(course)
            self.check_blacklist_expires(course)

        if self.need_print:
            print("\n".join(self.out_lines))
