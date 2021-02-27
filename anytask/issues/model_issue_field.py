# coding: utf-8

import inspect
import sys

from django.db import models
from issues.forms import IntForm, MarkForm, FileForm, CommentForm, get_responsible_form, get_followers_form, \
    get_status_form


class DefaultPlugin(object):
    PLUGIN_NAME = "DefaultPlugin"
    PLUGIN_VERSION = "1.0"


class FieldDefaultPlugin(DefaultPlugin):
    PLUGIN_NAME = "FieldDefaultPlugin"
    PLUGIN_VERSION = "1.0"
    FORM = IntForm

    @staticmethod
    def can_edit(field_name, user, issue):
        return issue.task.course.user_is_teacher(user)

    @classmethod
    def get_form(cls, *args, **kwargs):
        return cls.FORM(*args, **kwargs)

    @staticmethod
    def is_visible(field_name):
        return True

    @staticmethod
    def get_default_value(field_name):
        return None

    @staticmethod
    def get_value(issue):
        return None


class FieldCommentPlugin(FieldDefaultPlugin):
    PLUGIN_NAME = "FieldCommentPlugin"
    PLUGIN_VERSION = "1.0"
    FORM = CommentForm

    @classmethod
    def get_form(cls, *args, **kwargs):
        return cls.FORM(*(args[:3]), **kwargs)

    @staticmethod
    def is_visible(field_name):
        return False


class FieldMarkPlugin(FieldDefaultPlugin):
    PLUGIN_NAME = "FieldMarkPlugin"
    PLUGIN_VERSION = "1.0"
    FORM = MarkForm

    @classmethod
    def get_form(cls, *args, **kwargs):
        return cls.FORM(*(args[:3]), **kwargs)

    @staticmethod
    def get_default_value(field_name):
        return 0


class FieldStatusPlugin(FieldDefaultPlugin):
    PLUGIN_NAME = "FieldStatusPlugin"
    PLUGIN_VERSION = "1.0"

    @classmethod
    def get_form(cls, *args, **kwargs):
        return get_status_form(*args, **kwargs)


class FieldResponsiblePlugin(FieldDefaultPlugin):
    PLUGIN_NAME = "FieldResponsiblePlugin"
    PLUGIN_VERSION = "1.0"

    @classmethod
    def get_form(cls, *args, **kwargs):
        return get_responsible_form(*args, **kwargs)


class FieldFollowersPlugin(FieldDefaultPlugin):
    PLUGIN_NAME = "FieldFollowersPlugin"
    PLUGIN_VERSION = "1.0"

    @classmethod
    def get_form(cls, *args, **kwargs):
        return get_followers_form(*args, **kwargs)


class FieldFilePlugin(FieldDefaultPlugin):
    PLUGIN_NAME = "FieldFilePlugin"
    PLUGIN_VERSION = "1.0"
    FORM = FileForm

    @staticmethod
    def is_visible(field_name):
        return False


class FieldReadOnlyPlugin(FieldDefaultPlugin):
    PLUGIN_NAME = "FieldReadOnlyPlugin"
    PLUGIN_VERSION = "1.0"

    @staticmethod
    def can_edit(field_name, user, issue):
        return False


class IssueField(models.Model):
    name = models.CharField(max_length=191)
    title = models.CharField(max_length=191, blank=True)
    history_message = models.CharField(max_length=191, blank=True)
    plugin = models.CharField(max_length=191, default='FieldDefaultPlugin')
    plugin_version = models.CharField(max_length=50, default='0.1')

    _PLUGIN = dict()

    @classmethod
    def _init_plugins(cls):
        cls._PLUGIN[FieldDefaultPlugin.PLUGIN_NAME] = FieldDefaultPlugin()
        for name, obj in inspect.getmembers(sys.modules[__name__]):
            if not inspect.isclass(obj):
                continue

            if not issubclass(obj, FieldDefaultPlugin):
                continue

            cls._PLUGIN[obj.PLUGIN_NAME] = obj()

    def get_plugin(self):
        return self.__class__._PLUGIN[self.plugin]

    def get_default_value(self, *args, **kwargs):
        return self.get_plugin().get_default_value(self.name, *args, **kwargs)

    def get_form(self, *args, **kwargs):
        return self.get_plugin().get_form(self.name, *args, **kwargs)

    def can_edit(self, user, issue, *args, **kwargs):
        return self.get_plugin().can_edit(self.name, user, issue, *args, **kwargs)

    def is_visible(self, *args, **kwargs):
        return self.get_plugin().is_visible(self.name, *args, **kwargs)

    def is_loggable(self):
        return True

    def get_value(self, issue):
        return self.get_plugin().get_value(issue)

    def __str__(self):
        return u'{0}: {1}/{2} - {3}'.format(self.id, self.plugin, self.name, self.title)


IssueField._init_plugins()

# class FieldProperties(models.Model):
#     priority = models.IntegerField()
#     issue = models.ForeignKey(Issue)
#     field = models.ForeignKey(IssueField)
#     pass
