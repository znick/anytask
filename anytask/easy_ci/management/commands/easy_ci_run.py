import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from easy_ci.models import EasyCiTask, EasyCiCheck
from easy_ci.runner import CheckRunner

LOGGER = logging.getLogger('django.request')

class Command(BaseCommand):
    help = "Run EasyCI check"

    def handle(self, **options):
        for easy_ci_task in EasyCiTask.objects.filter(checked=False):
            runner = CheckRunner(easy_ci_task.data, easy_ci_task.task.title)

            actions = []
            if easy_ci_task.easycicheck_set.filter(type=EasyCiCheck.CHECK_ACTION_PEP8).count() == 0:
                actions.append(EasyCiCheck.CHECK_ACTION_PEP8)

            if easy_ci_task.easycicheck_set.filter(type=EasyCiCheck.CHECK_ACTION_TEST).count() == 0:
                actions.append(EasyCiCheck.CHECK_ACTION_TEST)

            LOGGER.info("EasyCiCron=1\tSTUDENT=%s\tTASK=%s\tACTIONS=%s", easy_ci_task.student.username, easy_ci_task.task.title, actions)

            for action in actions:
                with transaction.commit_on_success():
                    try:
                        exit_status, output = runner.run(action, easy_ci_task.student, easy_ci_task.task.group.name)
                    except Exception as e:
                        LOGGER.info("EasyCiCron=%s", e)
                        continue

                    easy_ci_check = EasyCiCheck()
                    easy_ci_check.easy_ci_task = easy_ci_task
                    easy_ci_check.type = action
                    easy_ci_check.exit_status = exit_status
                    easy_ci_check.output = output
                    easy_ci_check.save()

                    easy_ci_task.checked = True
                    easy_ci_task.save()
