from django.core.management.base import BaseCommand
from issues.models import Issue
from anyrb.common import AnyRB

import re

class Command(BaseCommand):
    help = "Fill in svn_path in issue (was not filled before because of a bug)"
    svn_path_re = re.compile("SVN: http://(?:.*?)/svn/(?:.*?)/(.*)", re.UNICODE)

    @classmethod
    def _get_svn_path_from_desc(cls, desc):
        svn_path = None
        for match in cls.svn_path_re.findall(desc):
            svn_path = match
        return svn_path

    def handle(self, **options):
        anyrb = AnyRB()
        root = anyrb.client.get_root()
        rb_id_x_issue = {}
        for issue in Issue.objects.all():
            if issue.rb_review_id not in rb_id_x_issue:
                rb_id_x_issue[issue.rb_review_id] = issue
                continue

            if issue.update_time > rb_id_x_issue[issue.rb_review_id].update_time:
                rb_id_x_issue[issue.rb_review_id] = issue

        for rb_id, issue in rb_id_x_issue.iteritems():
            try:
                review = root.get_review_request(review_request_id=rb_id)
            except Exception:
                print "{0}\tSKIPPED".format(issue)
                continue

            svn_path = self._get_svn_path_from_desc(review.description.encode("utf-8"))
            print "{0}\t{1}\t{2}".format(issue.student, rb_id, svn_path),
            if svn_path:
                issue.svn_path = svn_path
                issue.save()
                print " SAVED"
            else:
                print ""
