# -*- coding: utf-8 -*-

from courses.models import Course
from django.db import models


class PluginManager(models.Model):
    plugin_name = models.CharField(max_length=128, db_index=True)
    course = models.ForeignKey(Course, db_index=True)

    def get_course_plugins(self, course):
        for plugin in PluginManager.objects.filter(course=course):
            yield plugin.plugin_name

    def get_issue_plugin(self, issue):
        return self.get_course_plugins(issue.task.course)
