# -*- coding: utf-8 -*-

import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation, timezone
from django.utils.translation import ugettext as _
from django.db.models import Q

from anycontest.common import comment_verdict  # , set_contest_marks, convert_to_contest_login
from anycontest.models import ContestSubmission
from anyrb.common import AnyRB
from users.models import UserProfile


logger = logging.getLogger('django.request')


class Command(BaseCommand):
    help = "Check contest submissions and comment verdict"

    def handle(self, **options):
        start_time = time.time()
        contest_marks_len = 0
        contest_submissions = ContestSubmission.objects \
            .filter(Q(got_verdict=False) & (Q(send_error__isnull=True) | Q(send_error=""))) \
            .exclude(run_id__exact="") \
            .exclude(run_id__isnull=True)
        for contest_submission in contest_submissions:
            try:
                issue = contest_submission.issue
                task = issue.task
                lang = UserProfile.objects.get(user=contest_submission.author).language
                translation.activate(lang)

                comment = contest_submission.check_submission()
                if contest_submission.got_verdict:
                    if contest_submission.verdict == 'ok' and \
                            not task.course.send_rb_and_contest_together and \
                            task.rb_integrated:
                        anyrb = AnyRB(contest_submission.file.event)
                        review_request_id = anyrb.upload_review()
                        if review_request_id is not None:
                            comment += '\n' + u'<a href="{1}/r/{0}">Review request {0}</a>'. \
                                format(review_request_id, settings.RB_API_URL)
                        else:
                            comment += '\n' + _(u'oshibka_otpravki_v_rb')
                    if contest_submission.verdict == 'ok' and \
                            task.accepted_after_contest_ok and \
                            not issue.is_status_accepted():
                        if task.deadline_time and task.deadline_time < timezone.now() and \
                                task.course.issue_status_system.has_accepted_after_deadline():
                            issue.set_status_accepted_after_deadline()
                            if not issue.task.score_after_deadline:
                                comment += '\n' + _(u'bally_ne_uchityvautsia')
                        else:
                            issue.set_status_accepted()

                    if contest_submission.verdict == 'ok':
                        if issue.task.course.take_mark_from_contest:
                            contest_submission.get_contest_mark()
                            contest_marks_len += 1

                    comment_verdict(issue, contest_submission.verdict == 'ok', comment)
                translation.deactivate()
            except Exception as e:
                logger.exception(e)

        # for contest_id, students_info in contest_marks.iteritems():
        #     set_contest_marks(contest_id, students_info)

        # logging to cron log
        print("Command check_contest check {0} submissions ({1} - with marks) took {2} seconds"
              .format(len(contest_submissions), contest_marks_len, time.time() - start_time))
