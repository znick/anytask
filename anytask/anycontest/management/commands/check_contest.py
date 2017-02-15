# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.translation import ugettext as _
from anycontest.common import comment_verdict, get_contest_mark
from anyrb.common import AnyRB
from anycontest.models import ContestSubmission
from issues.model_issue_status import IssueStatus

import logging

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
                            comment += '\n' + _(u'Ошибка отправки в Review Board')
                    if contest_submission.verdict == 'ok' and task.accepted_after_contest_ok:
                        issue.set_status_by_tag(IssueStatus.STATUS_ACCEPTED)
                    if issue.task.course.id in settings.COURSES_WITH_CONTEST_MARKS:
                        student_profile = issue.student.get_profile()
                        if student_profile.ya_contest_login:
                            mark = get_contest_mark(task.contest_id, task.problem_id, student_profile.ya_contest_login)
                            if mark and float(mark) > 0:
                                issue.set_byname('mark', float(mark))
                    comment_verdict(issue, contest_submission.verdict == 'ok', comment)
            except Exception as e:
                logger.exception(e)
