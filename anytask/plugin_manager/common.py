# -*- coding: utf-8 -*-

import importlib
import json
from models import CourseModel, IssueModel
from settings_common import INSTALLED_APPS as apps


class PluginManager(object):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PluginManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.course_plugins = {}
        self.issue_plugins = {}
        self._set_plugins()

        self.plugins = {}
        for app in apps:
            try:
                if app.startwith('plugin'):
                    self.plugins[app] = importlib.import_module(app)
            except Exception:
                pass

    def _set_plugins(self):
        for course in CourseModel.objects.all():
            self.course_plugins[course.course_id] = json.loads(course.plugins)
        for issue in IssueModel.objects.all():
            self.issue_plugins[issue.issue_id] = json.loads(issue.plugins)

    def _get_course_plugins(self, course):
        try:
            return self.course_plugins[course]
        except Exception:
            pass
        finally:
            return json.loads(CourseModel.objects.get(course))

    def _get_issue_plugins(self, issue):
        try:
            return self.course_plugins[issue]
        except Exception:
            pass
        finally:
            return json.loads(IssueModel.objects.get(issue))

    def _work_views(self, course_plugins, issue_plugins):
        pass

    def _work_events(self, course_plugins, issue_plugins):
        pass

    def get_req_data(self, request):
        course = request.GET.get('course', None)
        issue = request.GET.get('issue', None)

        if course:
            course_plugins = self._get_course_plugins(course)

        if issue:
            issue_plugins = self._get_issue_plugins(issue)

        self._work_events(course_plugins=None, issue_plugins=None)
        self._work_views(course_plugins=None, issue_plugins=None)


    # def _get_course_data(self):
    #     pass
    #
    #
    # def get_data(self):
    #     for plg_id in self.plugins:
    #         plg_obj = ManagerStorage.objects.get(plg_id)
    #
    #         """
    #         Здесь используем мета программирование для извлечения нужного нам класса
    #         и применения нужного нам метода
    #         """
    #         plg_obj.meta_class.getattr()
    #
    #
    # def set_data(self, issue, data):
    #     pass


class BasicPlugin(object):

    def __init__(self):
        self.fields = {}

    def set(self, issue, field, value):
        pass

    def get(self, issue, field):
        pass




