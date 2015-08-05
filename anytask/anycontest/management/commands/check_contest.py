# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from anycontest.common import check_submission, comment_verdict

from issues.models import Event, Issue

class Command(BaseCommand):
    help = "Check contest submissions and comment verdict"

    def handle(self, **options):
        for issue in Issue.objects.filter(status=Issue.STATUS_AUTO_VERIFICATION):
            for event in issue.event_set.all():
                if event.issue.get_byname('run_id') != '':
                    get_verdict, verdict, comment = check_submission(issue)
                    if get_verdict:
                        comment_verdict(issue, verdict, comment)
