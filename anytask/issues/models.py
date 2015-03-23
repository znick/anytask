from datetime import datetime
from django.contrib.auth.models import User
from django.db import models

from tasks.models import Task


class Issue(models.Model):
    student = models.ForeignKey(User, db_index=True, null=False, blank=False)
    task = models.ForeignKey(Task, db_index=True, null=True, blank=False)

    rb_review_id = models.IntegerField(null=True, blank=True)
    svn_commit_id = models.IntegerField(null=True, blank=True)
    svn_path = models.CharField(max_length=254, null=True, blank=True)

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

    def __unicode__(self):
        return u"Issue: {0}_{1}_{2} rb: {3} svn: {4}".format(self.task.cource.year, self.task.title, self.student.get_full_name(), self.rb_review_id, self.svn_commit_id)
