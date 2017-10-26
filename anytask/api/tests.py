from __future__ import unicode_literals

import base64
import json

from django.core.urlresolvers import reverse

from courses.models import Course
from issues.models import Issue, IssueField, File
from tasks.models import Task
from users.models import Group
from years.models import Year

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import TestCase


class ApiTest(TestCase):
    maxDiff = None

    @classmethod
    def clean_timestamps(cls, x):
        if isinstance(x, list):
            for y in x:
                cls.clean_timestamps(y)
            return

        if not isinstance(x, dict):
            return

        x.pop("create_time", None)
        x.pop("update_time", None)
        x.pop("timestamp", None)

        for k, v in x.iteritems():
            cls.clean_timestamps(k)
            cls.clean_timestamps(v)

    def setUp(self):

        self.anytask_password = "anytask"
        self.anytask = User.objects.create_user(username='anytask',
                                                password=self.anytask_password)

        self.teacher_password = 'password1'
        self.teacher = User.objects.create_user(username='teacher',
                                                password=self.teacher_password)
        self.teacher.first_name = 'teacher_name'
        self.teacher.last_name = 'teacher_last_name'
        self.teacher.save()

        self.student_password = 'password2'
        self.student = User.objects.create_user(username='student',
                                                password=self.student_password)
        self.student.first_name = 'student_name'
        self.student.last_name = 'student_last_name'
        self.student.save()

        self.year = Year.objects.create(start_year=2016)

        self.group = Group.objects.create(name='group_name',
                                          year=self.year)
        self.group.students = [self.student]
        self.group.save()

        self.course = Course.objects.create(name='course_name',
                                            year=self.year)
        self.course.groups = [self.group]
        self.course.teachers = [self.teacher]
        self.course.issue_fields = IssueField.objects.exclude(id=10).exclude(id=11)
        self.course.save()

        self.task1 = Task.objects.create(title='task_title1',
                                         course=self.course,
                                         score_max=10)

        self.task2 = Task.objects.create(title='task_title2',
                                         course=self.course,
                                         score_max=20)

        self.issue1 = Issue.objects.create(task_id=self.task1.id, student_id=self.student.id)
        self.issue2 = Issue.objects.create(task_id=self.task2.id, student_id=self.student.id)
        self.issue2.responsible = self.teacher
        self.issue2.save()

        event = self.issue1.add_comment("Test comment")
        File.objects.create(file=SimpleUploadedFile('test_fail_rb.py', 'print "_failed_"'), event=event)

    def _request(self, username, password, method=None, *args, **kwargs):
        if method is None:
            method = self.client.get

        http_authorization = "basic " + \
                             base64.b64encode("{}:{}".format(username, password))

        kwargs.update({"HTTP_AUTHORIZATION": http_authorization})
        return method(*args, **kwargs)

    def test_get_issues(self):
        issues_list = [{u'status': u'New', u'task': {u'id': 1, u'title': u'task_title1'},
                        u'followers': [], u'student': {u'username': u'student', u'first_name': u'student_name',
                                                       u'last_name': u'student_last_name', u'middle_name': None,
                                                       u'name': u'student_name student_last_name', u'id': 3},
                        u'responsible': None, u'id': 1, u'mark': 0.0},
                       {u'status': u'New', u'task': {u'id': 2, u'title': u'task_title2'},
                        u'followers': [], u'student': {u'username': u'student', u'first_name': u'student_name',
                                                       u'last_name': u'student_last_name', u'middle_name': None,
                                                       u'name': u'student_name student_last_name', u'id': 3},
                        u'responsible': {u'username': u'teacher', u'first_name': u'teacher_name',
                                         u'last_name': u'teacher_last_name', u'middle_name': None,
                                         u'name': u'teacher_name teacher_last_name', u'id': 2},
                        u'id': 2, u'mark': 0.0}]
        response = self._request(self.teacher, self.teacher_password,
                                 path=reverse("api.views.get_issues", kwargs={"course_id": self.course.id}))
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.clean_timestamps(response_data)
        self.assertListEqual(issues_list, response_data)

    def test_get_issues__add_events(self):
        issues_list = [{u'status': u'New', u'task': {u'id': 1, u'title': u'task_title1'},
                        u'followers': [], u'student': {u'username': u'student', u'first_name': u'student_name',
                                                       u'last_name': u'student_last_name', u'middle_name': None,
                                                       u'name': u'student_name student_last_name', u'id': 3},
                        u'responsible': None, u'id': 1, u'mark': 0.0,
                        u'events': [{u'author': {u'first_name': u'',
                                                 u'id': 1,
                                                 u'last_name': u'',
                                                 u'middle_name': None,
                                                 u'name': u'',
                                                 u'username': u'anytask'},
                                     u'files': [{u'filename': u'test_fail_rb.py',
                                                 u'id': 1}],
                                     u'id': 1,
                                     u'message':
                                         u'<div class="contest-response-comment not-sanitize">Test comment</div>',
                                     u'timestamp': u'2017-10-26T05:29:33.287393+00:00Z'}]},
                       {u'status': u'New', u'task': {u'id': 2, u'title': u'task_title2'},
                        u'events': [],
                        u'followers': [], u'student': {u'username': u'student', u'first_name': u'student_name',
                                                       u'last_name': u'student_last_name', u'middle_name': None,
                                                       u'name': u'student_name student_last_name', u'id': 3},
                        u'responsible': {u'username': u'teacher', u'first_name': u'teacher_name',
                                         u'last_name': u'teacher_last_name', u'middle_name': None,
                                         u'name': u'teacher_name teacher_last_name', u'id': 2},
                        u'id': 2, u'mark': 0.0}]
        response = self._request(self.teacher, self.teacher_password,
                                 path=reverse("api.views.get_issues",
                                              kwargs={"course_id": self.course.id}) + "?add_events=1")
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.clean_timestamps(response_data)
        self.clean_timestamps(issues_list)

        url = response_data[0]['events'][0]['files'][0].pop("url")
        path = response_data[0]['events'][0]['files'][0].pop("path")
        self.assertIn("http", url)
        self.assertIn("/media/", url)
        self.assertIn("/media/", path)

        self.assertEqual(issues_list, response_data)

    def test_get_issues__not_teacher(self):
        response = self._request(self.student, self.student_password,
                                 path=reverse("api.views.get_issues", kwargs={"course_id": self.course.id}))
        self.assertEqual(response.status_code, 403)

    def test_get_issue(self, username=None, password=None):
        if not username:
            username = self.teacher
            password = self.teacher_password

        issue = {u'status': u'New', u'task': {u'id': 1, u'title': u'task_title1'},
                 u'followers': [], u'student': {u'username': u'student', u'first_name': u'student_name',
                                                u'last_name': u'student_last_name', u'middle_name': None,
                                                u'name': u'student_name student_last_name', u'id': 3},
                 u'events': [{
                     u'files': [
                         {
                             u'id': 1,
                             u'filename': u'test_fail_rb.py'}],
                     u'message': u'<div class="contest-response-comment not-sanitize">Test comment</div>',
                     u'id': 1,
                     u'author': {
                         u'username': u'anytask',
                         u'first_name': u'',
                         u'last_name': u'',
                         u'middle_name': None,
                         u'name': u'',
                         u'id': 1}}],
                 u'responsible': None, u'id': 1, u'mark': 0.0}

        response = self._request(username, password,
                                 path=reverse("api.views.get_issue", kwargs={"issue_id": self.issue1.id}))
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.clean_timestamps(response_data)

        url = response_data['events'][0]['files'][0].pop("url")
        path = response_data['events'][0]['files'][0].pop("path")
        self.assertIn("http", url)
        self.assertIn("/media/", url)
        self.assertIn("/media/", path)

        self.assertDictEqual(issue, response_data)

        response = self.client.get(url)
        self.assertEqual('print "_failed_"', response.content)

    def test_get_issue_no_access(self):
        response = self._request(self.anytask, self.anytask_password,
                                 path=reverse("api.views.get_issues", kwargs={"course_id": self.course.id}))
        self.assertEqual(response.status_code, 403)

    def test_get_issue_student_has_access(self):
        self.test_get_issue(self.student, self.student_password)

    def test_post_comment(self):
        username = self.teacher
        password = self.teacher_password

        response = self._request(username, password,
                                 path=reverse("api.views.add_comment", kwargs={"issue_id": self.issue1.id}),
                                 method=self.client.post, data={"comment": "Hello from test"})
        self.assertEqual(response.status_code, 201)

        response = self._request(username, password,
                                 path=reverse("api.views.get_issue", kwargs={"issue_id": self.issue1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello from test")

    def test_post_comment__no_access(self):
        response = self._request(self.anytask, self.anytask_password,
                                 path=reverse("api.views.add_comment", kwargs={"issue_id": self.issue1.id}),
                                 method=self.client.post, data={"comment": "No access"})
        self.assertEqual(response.status_code, 403)

        response = self._request(self.teacher, self.teacher_password,
                                 path=reverse("api.views.get_issue", kwargs={"issue_id": self.issue1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "No access")
