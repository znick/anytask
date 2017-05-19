from django.db import models
from django.core.urlresolvers import reverse
from courses.models import Course
from django.db.models.signals import post_save

from permissions.models import PermissionBase, RolesVisible
from guardian.models import GroupObjectPermissionBase, UserObjectPermissionBase


class School(models.Model):
    name = models.CharField(max_length=191, db_index=True, null=False, blank=False)
    link = models.CharField(max_length=191, db_index=False, null=False, blank=False)
    courses = models.ManyToManyField(Course, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.name)

    def get_absolute_url(self):
        return reverse('schools.views.school_page', args=[str(self.link)])

    class Meta:
        permissions = (
            ('view_permissions', 'View permissions'),
            ('change_permissions', 'Change permissions'),
            ('view_users_status_filter', 'View users status filter'),
            ('change_user_status', 'Change users statuses'),
        )


class SchoolUserObjectPermission(UserObjectPermissionBase, PermissionBase):
    content_object = models.ForeignKey(School, on_delete=models.CASCADE)


class SchoolGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(School, on_delete=models.CASCADE)


def create_role_visible(sender, instance, created, **kwargs):
    if created:
        RolesVisible.objects.get_or_create(school=instance)


post_save.connect(create_role_visible, sender=School)
