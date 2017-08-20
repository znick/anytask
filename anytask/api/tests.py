"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import base64
import json

from django.core.urlresolvers import reverse

from api.views import unpack_issue
from courses.models import Course
from issues.models import Issue, IssueField
from tasks.models import Task
from users.models import Group
from years.models import Year

from django.contrib.auth.models import User

from django.test import TestCase


class ApiTest(TestCase):
    def setUp(self):
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

    def _get(self, username, password, *args, **kwargs):

        http_authorization = "basic " + \
                             base64.b64encode("{}:{}".format(username, password))

        kwargs.update({"HTTP_AUTHORIZATION": http_authorization})
        return self.client.get(*args, **kwargs)

    def test_get_issues(self):
        issues_list = map(unpack_issue, [self.issue1, self.issue2])

        response = self._get(self.teacher, self.teacher_password,
                             reverse("api.views.get_issues", kwargs={"course_id": self.course.id}))
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertListEqual(issues_list, response_data)

    def test_get_issues__not_teacher(self):
        response = self._get(self.student, self.student_password,
                             reverse("api.views.get_issues", kwargs={"course_id": self.course.id}))
        self.assertEqual(response.status_code, 403)
