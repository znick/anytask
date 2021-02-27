# -*- coding: utf-8 -*-

import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail

from django.contrib.sites.models import Site
from anycontest.models import ContestSubmission

from datetime import timedelta

logger = logging.getLogger('django.request')


class Command(BaseCommand):
    help = "Check contest submissions with no answer"

    def handle(self, **options):
        start_time = time.time()
        contest_submissions = ContestSubmission.objects \
            .filter(Q(got_verdict=False) & (Q(send_error__isnull=True) | Q(send_error=""))) \
            .exclude(run_id__exact="") \
            .exclude(run_id__isnull=True) \
            .filter(create_time__lt=timezone.now() - timedelta(minutes=settings.FREEZED_RUN_ID_MINUTES)) \
            .filter(sended_notify=False)
        subject = "Problems with contests submissions"
        message = ""
        email = settings.RESPONSIBLE_EMAIL if hasattr(settings, 'RESPONSIBLE_EMAIL') else settings.DEFAULT_FROM_EMAIL
        domain = Site.objects.get_current().domain

        for contest_submission in contest_submissions:
            issue = contest_submission.issue

            message += u"Issue:\t\t{0}{1}\n".format(domain, issue.get_absolute_url())
            message += u"Run info:\thttps://contest.yandex.ru/contest/{1}/run-report/{0}\n".format(
                contest_submission.run_id,
                issue.task.contest_id,
            )
            message += u"Run info full:\thttps://contest.yandex.ru/admin/run-report?id={0}\n".format(
                contest_submission.run_id,
            )
            message += u"Time created:\t{0}\n".format(contest_submission.create_time.strftime("%d-%m-%Y %H:%M:%S"))
            message += u"Time delta:\t{0}\n".format(timezone.now() - contest_submission.create_time)
            # message += u"Last contest response:\t{0} \n".format(contest_submission.full_response)
            message += u"\n\n"

            contest_submission.sended_notify = True
            contest_submission.save()

        if message:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email, "anytask@yandex.ru"])

        # logging to cron log
        print("Command send_freezed_run_id_notify check {0} submissions took {1} seconds"
              .format(len(contest_submissions), time.time() - start_time))
