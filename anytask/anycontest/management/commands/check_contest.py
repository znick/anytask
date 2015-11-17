# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from anycontest.common import check_submission, comment_verdict
from anyrb.common import AnyRB
from issues.models import Event, Issue

import logging

logger = logging.getLogger('django.request')

class Command(BaseCommand):
    help = "Check contest submissions and comment verdict"

    def handle(self, **options):
        for issue in Issue.objects.filter(status=Issue.STATUS_AUTO_VERIFICATION):
            try:
                run_id = issue.get_byname('run_id')
                events = issue.event_set.all().reverse()
                for event_id,event in enumerate(events):
                    if event.value == run_id:
                        got_verdict, verdict, comment = check_submission(issue)
                        if got_verdict:
                            if verdict and not issue.task.course.send_rb_and_contest_together and issue.task.course.rb_integrated:
                                anyrb = AnyRB(events[event_id-1])
                                review_request_id = anyrb.upload_review()
                                if review_request_id is not None:
                                    comment += '\n' + \
                                              u'<a href="{1}/r/{0}">Review request {0}</a>'. \
                                              format(review_request_id,settings.RB_API_URL)
                                else:
                                    comment += u'Ошибка отправки в Review Board.'
                            comment_verdict(issue, verdict, comment)
            except Exception as e:
                logger.exception(e)