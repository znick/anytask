from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
from datetime import datetime

from years.models import Year

from permissions.models import PermissionBase
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase

class Group(models.Model):
    year = models.ForeignKey(Year, db_index=True, null=False, blank=True)
    name = models.CharField(max_length=191, db_index=True, null=False, blank=True)
    students = models.ManyToManyField(User, null=True, blank=True)

    added_time = models.DateTimeField(auto_now_add=True, default=datetime.now)
    update_time = models.DateTimeField(auto_now=True, default=datetime.now)

    class Meta:
        unique_together = (("year", "name"),)
        permissions = (
            ('student_in_group', 'Student in group'),
            ('view_gradebook', 'View gradebook'),
            ('create_task', 'Create task'),
            ('view_task_settings', 'View task settings'),
            ('change_task_title', 'Change task title'),
            ('change_task_groups', 'Change task groups'),
            ('change_task_is_hidden', 'Change task is_hidden'),
            ('change_task_parent_task', 'Change task parent task'),
            ('change_task_task_text', 'Change task task_text'),
            ('change_task_score_max', 'Change task score_max'),
            ('change_task_contest', 'Change task contest'),
            ('change_task_rb', 'Change task rb'),
            ('change_task_type', 'Change task type'),
            ('change_task_deadline_time', 'Change task deadline_time'),
            ('change_task_one_file_upload', 'Change task one_file_upload'),
        )

    def __unicode__(self):
        return u"{0}|{1}".format(self.year, unicode(self.name))



class GroupUserObjectPermission(UserObjectPermissionBase, PermissionBase):
    content_object = models.ForeignKey(Group, on_delete=models.CASCADE)


class GroupGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Group, on_delete=models.CASCADE)
