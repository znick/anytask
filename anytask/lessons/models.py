# coding: utf-8

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from courses.models import Course
from groups.models import Group


class Lesson(models.Model):
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True, default=None)
    date_starttime = models.DateTimeField(auto_now=False, null=True, default=None)
    date_endtime = models.DateTimeField(auto_now=False, null=True, default=None)
    course = models.ForeignKey(Course, db_index=True, null=False, blank=False)
    groups = models.ManyToManyField(Group, null=False, blank=False)
    visited_students = models.ManyToManyField(User, null=True, blank=True)
    updated_by = models.ForeignKey(User, db_index=False, null=True, blank=True, related_name='authors')
    schedule_id = models.IntegerField(db_index=True, null=True, blank=True)

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

    def set_position_in_new_group(self, groups=None):
        if not groups:
            groups = self.course.groups.all()
        else:
            for lssn_related in LessonGroupRelations.objects.filter(lesson=self).exclude(group__in=groups):
                lssn_related.deleted = True
                lssn_related.save()

        for group in list(groups):
            lssn_related, created = LessonGroupRelations.objects.get_or_create(lesson=self, group=group)

            if created:
                lssn_related.position = int(self.date_starttime.strftime('%Y%m%d%H%M'))
            else:
                lssn_related.deleted = False
            lssn_related.save()


class LessonGroupRelations(models.Model):
    lesson = models.ForeignKey(Lesson, db_index=False, null=False, blank=False)
    group = models.ForeignKey(Group, db_index=False, null=False, blank=False)
    position = models.IntegerField(db_index=False, null=False, blank=False, default=0)
    deleted = models.BooleanField(db_index=False, null=False, blank=False, default=False)

    class Meta:
        unique_together = ("lesson", "group")

    def __unicode__(self):
        return ' '.join([unicode(self.lesson), unicode(self.group), unicode(self.position)])