# -*- coding: utf-8 -*-

import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail

from django.contrib.sites.models import Site
from issues.models import Issue

from collections import defaultdict

logger = logging.getLogger('django.request')


class Command(BaseCommand):
    help = "Send email about duplicate issue"

    option_list = BaseCommand.option_list

    def handle(self, **options):
        start_time = time.time()

        issues_duplicates = defaultdict(list)
        domain = Site.objects.get_current().domain

        for info in Issue.objects.values("id", "student_id", "task_id"):
            key = (info["student_id"], info["task_id"])
            issues_duplicates[key].append(info["id"])

        subject = "Duplicate issue"
        message = ""
        issues_len = 0
        for key, issues_ids in issues_duplicates.items():
            if len(issues_ids) > 1:
                issues_len += 1
                for issue_id in issues_ids:
                    message += u"Issue:\t{0}\n".format(domain + '/admin/issues/issue/' + str(issue_id))
                message += u"\n" + u"*" * 20 + u"\n\n"

        if message:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, ["anytask@yandex.ru"])

        # logging to cron log
        print("Command send_issue_duplicate_notify find {0} issues and took {1} seconds"
              .format(issues_len, time.time() - start_time))
