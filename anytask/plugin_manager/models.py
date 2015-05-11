# -*- coding: utf-8 -*-

import json
from django.db import models


# class ManagerStorage(models.Model):
#
#     issue = models.IntegerField()
#     meta_class = models.CharField()
#     meta_functions = models.CharField()

class MixinModel(models.Model):

    plugins = models.TextField(default='[]')

    def add_plugin(self, plugin):
        plugins_lst = json.loads(self.plugins)
        plugins_lst.add(plugin)
        self.plugins = json.dumps(plugins_lst)
        self.save()


class IssueModel(MixinModel):

    issue_id = models.IntegerField()


class CourseModel(MixinModel):

    course_id = models.IntegerField()

