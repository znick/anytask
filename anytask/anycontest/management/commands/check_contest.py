# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from anycontest.common import check_submission, comment_verdict
from anyrb.common import AnyRB
from issues.models import Event, Issue

class Command(BaseCommand):
    help = "Check contest submissions and comment verdict"

    def handle(self, **options):
        for issue in Issue.objects.filter(status=Issue.STATUS_AUTO_VERIFICATION):
            run_id = issue.get_byname('run_id')
            if run_id != '':
                for event in issue.event_set.all().reverse():
                    if event.value == run_id:
                        got_verdict, verdict, comment = check_submission(issue)
                        if got_verdict:
                            if verdict and not issue.task.course.send_rb_and_contest_together and issue.task.course.rb_integrated:
                                anyrb = AnyRB(event.get_previous_by_timestamp())
                                anyrb.upload_review()
                                comment += '\n' + \
                                          u'<a href="{1}/r/{0}">Review request {0}</a>'. \
                                          format(issue.get_byname('review_id'),settings.RB_API_URL)
                            comment_verdict(issue, verdict, comment)
