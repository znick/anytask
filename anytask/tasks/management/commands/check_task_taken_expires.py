#!/usr/bin/python
from django.core.management.base import BaseCommand, CommandError
import datetime
from django.db.models import Q

from cources.models import Cource
from tasks.models import TaskTaken


class Command(BaseCommand):
    help = 'Task taken clenup'

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.out_lines = []
        self.need_print = False

    def check_cource_task_taken_expires(self, cource):
        if not cource.max_days_without_score:
            return

        task_expired_date = datetime.datetime.now() - datetime.timedelta(days=cource.max_days_without_score)
        for task in cource.task_set.all():
            task_taken_query = TaskTaken.objects.filter(task=task)
            task_taken_query = task_taken_query.filter(Q(Q(status=TaskTaken.STATUS_TAKEN) | Q(status=TaskTaken.STATUS_CANCELLED)))
            task_taken_query = task_taken_query.filter(added_time__lte = task_expired_date)

            task_taken_to_delete = []
            task_taken_to_blacklist = []
            for task_taken in task_taken_query:
                if task_taken.status == TaskTaken.STATUS_TAKEN:
                    self.out_lines.append(">Blacklisting task_taken : {0}".format(task_taken))
                    self.need_print = True
                    task_taken_to_blacklist.append(task_taken)

                if task_taken.status == TaskTaken.STATUS_CANCELLED:
                    self.out_lines.append(">Dropping task_taken : {0}".format(task_taken))
                    self.need_print = True
                    task_taken_to_delete.append(task_taken)

            for task_taken in task_taken_to_blacklist:
                task_taken.status = TaskTaken.STATUS_BLACKLISTED
                task_taken.save()

            for task_taken in task_taken_to_delete:
                task_taken.delete()

    def check_blacklist_expires(self, cource):
        blacklist_expired_date = datetime.datetime.now() - datetime.timedelta(days=cource.days_drop_from_blacklist)

        for task in cource.task_set.all():
            task_taken_query = TaskTaken.objects.filter(task=task)
            task_taken_query = task_taken_query.filter(status=TaskTaken.STATUS_BLACKLISTED)
            task_taken_query = task_taken_query.filter(update_time__lte = blacklist_expired_date)

            task_taken_to_delete = []
            for task_taken in task_taken_query:
                self.out_lines.append(">Dropping task_taken : {0}".format(task_taken))
                self.need_print = True
                task_taken_to_delete.append(task_taken)

            for task_taken in task_taken_to_delete:
                task_taken.delete()

    def handle(self, *args, **options):
        for cource in Cource.objects.filter(type=Cource.TAKE_POLICY_SELF_TAKEN):
            self.out_lines.append("Cource '{0}'".format(cource))
            if cource.max_days_without_score:
                self.check_cource_task_taken_expires(cource)
            else:
                self.out_lines.append("max_days_without_score == 0 - Course skipped for check_cource_task_taken_expires")
            self.check_blacklist_expires(cource)

        if self.need_print:
            print "\n".join(self.out_lines)
