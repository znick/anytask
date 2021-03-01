# coding: utf-8

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from courses.models import Course
from groups.models import Group


class Lesson(models.Model):
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True, default='')
    date_starttime = models.DateTimeField(auto_now=False, null=True, default=None)
    date_endtime = models.DateTimeField(auto_now=False, null=True, default=None)
    course = models.ForeignKey(Course, db_index=True, null=False, blank=False)
    group = models.ForeignKey(Group, null=False, blank=False)
    not_visited_students = models.ManyToManyField(User, blank=True)
    updated_by = models.ForeignKey(User, db_index=False, null=True, blank=True, related_name='authors')
    schedule_id = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    position = models.IntegerField(db_index=True, null=True, blank=True)

    PERIOD_SIMPLE = 'Once'
    PERIOD_WEEK = 'Weekly'
    PERIOD_MONTH = 'Monthly'

    PERIOD_CHOICES = (
        (PERIOD_SIMPLE, _('odin_raz')),
        (PERIOD_WEEK, _('ezhenedelno'))
    )

    period = models.CharField(db_index=False, max_length=128, choices=PERIOD_CHOICES, default=PERIOD_SIMPLE)
    date_end = models.DateTimeField(auto_now=False, null=True, default=None)
    days = models.CharField(max_length=100, db_index=True, null=True, blank=True)

    def __unicode__(self):
        return unicode(self.title)

    def set_position(self):
        self.position = int(self.date_starttime.strftime('%y%m%d%H%M'))
        self.save()
