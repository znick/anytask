# -*- coding: utf-8 -*-

import logging
import time
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import atomic as commit_on_success
from django.utils import translation

from issues.models import Issue

from anycontest.common import get_problem_compilers

logger = logging.getLogger('django.request')


def write_message(header, message):
    return "{0}:\t{1}\n".format(header, message)


def get_compiler(file_name, problem_compilers):
    chosen_compiler = ""
    for ext in settings.CONTEST_EXTENSIONS:
        filename, extension = os.path.splitext(file_name)
        if ext == extension:
            if not problem_compilers:
                chosen_compiler = settings.CONTEST_EXTENSIONS[ext]
            if settings.CONTEST_EXTENSIONS[ext] in problem_compilers:
                chosen_compiler = settings.CONTEST_EXTENSIONS[ext]
                problem_compilers.remove(chosen_compiler)
    return chosen_compiler


class Command(BaseCommand):
    args = '<file_name>'
    help = "Send file to contest in specified issues if not yet"

    option_list = BaseCommand.option_list

    @commit_on_success
    def handle(self, *args, **options):
        start_time = time.time()

        if len(args) == 0:
            print("Specify file name")
            return

        with open(args[0], 'r') as f:
            issues_ids = set(f.read().splitlines())

        issues = Issue.objects.filter(id__in=issues_ids)
        issues_ids_used = set()
        problem_compilers_used = {}
        message = "Log\n"
        for issue in issues:
            contest_id = issue.task.contest_id
            problem_id = issue.task.problem_id

            if not issue.task.contest_integrated or not contest_id or not problem_id:
                message += write_message(issue.id, "No contest settings in task")
                continue

            if issue.contestsubmission_set.exists():
                message += write_message(issue.id, "Already have contest submissions")
                continue

            old_event = issue.event_set.filter(field__name='file').exclude(file__isnull=True).order_by("-timestamp")
            if len(old_event) == 0:
                message += write_message(issue.id, "No file submissions in issue")
                continue

            old_event = old_event[0]
            file = old_event.file_set.all()[0]

            problem_compilers_key = (problem_id, contest_id)
            if problem_compilers_key in problem_compilers_used:
                problem_compilers = get_problem_compilers(issue.task.problem_id, issue.task.contest_id)
            else:
                problem_compilers = get_problem_compilers(issue.task.problem_id, issue.task.contest_id)
                problem_compilers_used[problem_compilers_key] = problem_compilers
            chosen_compiler = get_compiler(file.file.name, problem_compilers)

            if not chosen_compiler:
                message += write_message(issue.id, "Can't determinate compiler")
                continue
            event_value = {'files': [], 'comment': '', 'compilers': []}

            event_value['files'].append(file.file)
            event_value['compilers'].append(chosen_compiler)

            translation.activate(issue.student.profile.language)
            issue.set_byname('comment', event_value, issue.student)
            translation.deactivate()

            issues_ids_used.add(str(issue.id))
            message += write_message(issue.id, "Completed!")

        message += "Fixed: {0}/{1}\nNot fixed issues: {2}\nTime: {3}".format(
            len(issues_ids_used),
            len(issues_ids),
            ", ".join(issues_ids - issues_ids_used),
            time.time() - start_time
        )

        print(message)
