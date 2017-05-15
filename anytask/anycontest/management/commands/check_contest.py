# -*- coding: utf-8 -*-

import logging
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation
from django.utils.translation import ugettext as _

from anycontest.common import comment_verdict, get_contest_mark
from anycontest.models import ContestSubmission
from anyrb.common import AnyRB
from users.models import UserProfile

logger = logging.getLogger('django.request')


class Command(BaseCommand):
    help = "Check contest submissions and comment verdict"

    def handle(self, **options):
        for contest_submission in ContestSubmission.objects \
                .filter(got_verdict=False, send_error__isnull=True) \
                .exclude(run_id__exact="") \
                .exclude(run_id__isnull=True):
            try:
                issue = contest_submission.issue
                run_id = contest_submission.run_id
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
                            comment += '\n' + \
                                       u'<a href="{1}/r/{0}">Review request {0}</a>'. \
                                           format(review_request_id, settings.RB_API_URL)
                        else:
                            comment += '\n' + _(u'oshibka_otpravki_v_rb')
                    if contest_submission.verdict == 'ok' and \
                            task.accepted_after_contest_ok and \
                            not issue.is_status_accepted():
                        if task.deadline_time and task.deadline_time < datetime.now() and \
                                task.course.issue_status_system.has_accepted_after_deadline():
                            issue.set_status_accepted_after_deadline()
                            if not issue.task.score_after_deadline:
                                comment += '\n' + _(u'bally_ne_uchityvautsia')
                        else:
                            issue.set_status_accepted()
                    if issue.task.course.id in settings.COURSES_WITH_CONTEST_MARKS:
                        student_profile = issue.student.get_profile()
                        if student_profile.ya_contest_login:
                            mark = get_contest_mark(task.contest_id, task.problem_id, student_profile.ya_contest_login)
                            if mark and float(mark) > 0:
                                issue.set_byname('mark', float(mark))
                    comment_verdict(issue, contest_submission.verdict == 'ok', comment)
                translation.deactivate()
            except Exception as e:
                logger.exception(e)

