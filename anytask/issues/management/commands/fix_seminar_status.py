# -*- coding: utf-8 -*-

import logging
import time
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db.transaction import atomic as commit_on_success
from django.contrib.auth.models import User
from django.db.models import Sum

from issues.models import Issue, IssueStatus
from tasks.models import Task

logger = logging.getLogger('django.request')


def get_mark(task_id, student_id):
    return (Issue.objects
            .filter(task__parent_task_id=task_id, student_id=student_id)
            .exclude(task__is_hidden=True)
            .exclude(task__score_after_deadline=False, status_field__tag=IssueStatus.STATUS_ACCEPTED_AFTER_DEADLINE)
            .aggregate(Sum('mark'))['mark__sum'] or 0)


class Command(BaseCommand):
    help = "Set status seminar for seminar issues and sum scores"

    option_list = BaseCommand.option_list + (
        make_option(
            '--fix-all',
            action='store_true',
            default=False,
            help='Synced all seminar marks and create missing issues'
        ),
        make_option(
            '--only-check',
            action='store_true',
            default=False,
            help='Check all seminar marks'
        ),
    )

    @commit_on_success
    def handle(self, **options):
        start_time = time.time()

        issues = []
        student_ids = []
        issues_synced = 0
        issues_created = 0
        issues_changed = 0
        if not options['fix_all']:
            issues = Issue.objects \
                .filter(task__type=Task.TYPE_SEMINAR) \
                .exclude(status_field__tag=IssueStatus.STATUS_SEMINAR)

            for issue in issues:
                issue.set_status_seminar()
        else:
            student_ids = User.objects.exclude(group__isnull=True).distinct().values_list('id', flat=True)
            for i, student_id in enumerate(student_ids):
                tasks_ids = Task.objects \
                    .filter(groups__students__id=student_id, type=Task.TYPE_SEMINAR) \
                    .distinct() \
                    .values_list('id', flat=True)
                for j, task_id in enumerate(tasks_ids):
                    new_mark = get_mark(task_id, student_id)
                    old_mark = 0
                    created = False
                    if options['only_check']:
                        try:
                            issue = Issue.objects.get(task_id=task_id, student_id=student_id)
                            old_mark = issue.mark
                        except Issue.DoesNotExist:
                            created = True
                    else:
                        issue, created = Issue.objects.get_or_create(task_id=task_id, student_id=student_id)
                        old_mark = issue.mark
                        issue.mark = get_mark(task_id, student_id)
                        issue.set_status_seminar()

                    if old_mark != new_mark:
                        issues_changed += 1
                    if created:
                        issues_created += 1
                    issues_synced += 1

                    print("Student: {0}/{1}\tSeminar: {2}/{3}\tCreated: {4}\tChanged: {5}"
                          .format(i + 1, len(student_ids), j + 1, len(tasks_ids), created, old_mark != new_mark))

        print("Command fix_seminar_status fixed status for {0} issues, synced {1} issues "
              "(changed mark {2} issues, created {3} issues) for {4} students and took {5} seconds").format(
            len(issues),
            issues_synced,
            issues_changed,
            issues_created,
            len(student_ids),
            time.time() - start_time
        )
