# coding: utf-8

from django.db import models
from django.db.models import Max
from django.contrib.auth.models import User

from courses.models import Course
from groups.models import Group


class Lesson(models.Model):
    title = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True, default=None)
    lesson_date = models.DateTimeField(auto_now=False, null=True, default=None)
    course = models.ForeignKey(Course, db_index=True, null=False, blank=False)
    groups = models.ManyToManyField(Group, null=False, blank=False, related_name='lesson_groups')
    visited_students = models.ManyToManyField(User, null=True, blank=True)
    updated_by = models.ForeignKey(User, db_index=False, null=True, blank=True, related_name='authors')

    def __unicode__(self):
        return unicode(self.title)

    def has_issue_access(self):
        return False

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
                max_position = LessonGroupRelations.objects.filter(group=group).exclude(id=lssn_related.id)\
                    .aggregate(Max('position'))['position__max']
                lssn_related.position = max_position + 1 if max_position is not None else 0
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