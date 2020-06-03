from __future__ import unicode_literals

import base64
import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase

from courses.models import Course
from issues.model_issue_status import IssueStatus
from issues.models import Issue, IssueField, File
from tasks.models import Task
from users.models import Group
from years.models import Year

import api.views


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

        for k, v in iter(x.items()):
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
        self.course.issue_status_system.statuses = IssueStatus.objects.all()
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
        File.objects.create(file=SimpleUploadedFile('test_fail_rb.py', b'print "_failed_"'), event=event)

    def _request(self, username, password, method=None, *args, **kwargs):
        if method is None:
            method = self.client.get

        http_authorization = "basic " + base64.b64encode("{}:{}".format(username, password)
                                                         .encode('utf8')).decode('utf8')

        kwargs.update({"HTTP_AUTHORIZATION": http_authorization})
        return method(*args, **kwargs)

    def test_get_issues(self):
        issues_list = [
            {
                'status': {
                    'color': '#818A91',
                    'tag': 'new',
                    'id': 1,
                    'name': 'New'
                },
                'task': {
                    'id': 1,
                    'title': 'task_title1'
                },
                'responsible': None,
                'mark': 0.0,
                'followers': [],
                'student': {
                    'username': 'student',
                    'first_name': 'student_name',
                    'last_name': 'student_last_name',
                    'middle_name': None,
                    'name': 'student_name student_last_name',
                    'id': 3
                },
                'id': 1
            },
            {
                'status': {
                    'color': '#818A91',
                    'tag': 'new',
                    'id': 1,
                    'name': 'New'
                },
                'task': {
                    'id': 2,
                    'title': 'task_title2'
                },
                'responsible': {
                    'username': 'teacher',
                    'first_name': 'teacher_name',
                    'last_name': 'teacher_last_name',
                    'middle_name': None,
                    'name': 'teacher_name teacher_last_name',
                    'id': 2
                },
                'mark': 0.0,
                'followers': [],
                'student': {
                    'username': 'student',
                    'first_name': 'student_name',
                    'last_name': 'student_last_name',
                    'middle_name': None,
                    'name': 'student_name student_last_name',
                    'id': 3
                },
                'id': 2
            }
        ]
        response = self._request(self.teacher, self.teacher_password,
                                 path=reverse(api.views.get_issues, kwargs={"course_id": self.course.id}))

        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.clean_timestamps(response_data)
        self.assertListEqual(issues_list, response_data)

    def test_get_issues__add_events(self):
        issues_list = [
            {
                'status': {
                    'color': '#818A91',
                    'tag': 'new',
                    'id': 1,
                    'name': 'New'
                },
                'task': {
                    'id': 1,
                    'title': 'task_title1'
                },
                'responsible': None,
                'id': 1,
                'followers': [],
                'student': {
                    'username': 'student',
                    'first_name': 'student_name',
                    'last_name': 'student_last_name',
                    'middle_name': None,
                    'name': 'student_name student_last_name',
                    'id': 3
                },
                'mark': 0.0,
                'events': [
                    {
                        'files': [
                            {
                                'id': 1,
                                'filename': 'test_fail_rb.py'
                            }
                        ],
                        'message': '<div class="contest-response-comment not-sanitize">Test comment</div>',
                        'id': 1,
                        'author': {
                            'username': 'anytask',
                            'first_name': '',
                            'last_name': '',
                            'middle_name': None,
                            'name': '',
                            'id': 1
                        }
                    }
                ]
            },
            {
                'status': {
                    'color': '#818A91',
                    'tag': 'new',
                    'id': 1,
                    'name': 'New'
                },
                'task': {
                    'id': 2,
                    'title': 'task_title2'
                },
                'responsible': {
                    'username': 'teacher',
                    'first_name': 'teacher_name',
                    'last_name': 'teacher_last_name',
                    'middle_name': None,
                    'name': 'teacher_name teacher_last_name',
                    'id': 2
                },
                'id': 2,
                'followers': [],
                'student': {
                    'username': 'student',
                    'first_name': 'student_name',
                    'last_name': 'student_last_name',
                    'middle_name': None,
                    'name': 'student_name student_last_name',
                    'id': 3
                },
                'mark': 0.0,
                'events': []
            }
        ]

        response = self._request(self.teacher, self.teacher_password,
                                 path=reverse(api.views.get_issues,
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
                                 path=reverse(api.views.get_issues, kwargs={"course_id": self.course.id}))
        self.assertEqual(response.status_code, 403)

    def test_get_issue(self, username=None, password=None):
        if not username:
            username = self.teacher
            password = self.teacher_password

        issue = {
            'status': {
                'color': '#818A91',
                'tag': 'new',
                'id': 1,
                'name': 'New'
            },
            'task': {
                'id': 1,
                'title': 'task_title1'
            },
            'responsible': None,
            'id': 1,
            'followers': [],
            'student': {
                'username': 'student',
                'first_name': 'student_name',
                'last_name': 'student_last_name',
                'middle_name': None,
                'name': 'student_name student_last_name',
                'id': 3
            },
            'mark': 0.0,
            'events': [
                {
                    'files': [
                        {
                            'id': 1,
                            'filename': 'test_fail_rb.py'
                        }
                    ],
                    'message': '<div class="contest-response-comment not-sanitize">Test comment</div>',
                    'id': 1,
                    'author': {
                        'username': 'anytask',
                        'first_name': '',
                        'last_name': '',
                        'middle_name': None,
                        'name': '',
                        'id': 1
                    }
                }
            ]
        }
        response = self._request(username, password,
                                 path=reverse(api.views.get_or_post_issue, kwargs={"issue_id": self.issue1.id}))
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
        self.assertEqual(b'print "_failed_"', b''.join(response.streaming_content))

    def test_get_issue_no_access(self):
        response = self._request(self.anytask, self.anytask_password,
                                 path=reverse(api.views.get_issues, kwargs={"course_id": self.course.id}))
        self.assertEqual(response.status_code, 403)

    def test_get_issue_student_has_access(self):
        self.test_get_issue(self.student, self.student_password)

    def test_post_comment(self):
        username = self.teacher
        password = self.teacher_password

        response = self._request(username, password,
                                 path=reverse(api.views.add_comment, kwargs={"issue_id": self.issue1.id}),
                                 method=self.client.post, data={"comment": "Hello from test"})
        self.assertEqual(response.status_code, 201)

        response = self._request(username, password,
                                 path=reverse(api.views.get_or_post_issue, kwargs={"issue_id": self.issue1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello from test")

    def test_post_comment__no_access(self):
        response = self._request(self.anytask, self.anytask_password,
                                 path=reverse(api.views.add_comment, kwargs={"issue_id": self.issue1.id}),
                                 method=self.client.post, data={"comment": "No access"})
        self.assertEqual(response.status_code, 403)

        response = self._request(self.teacher, self.teacher_password,
                                 path=reverse(api.views.get_or_post_issue, kwargs={"issue_id": self.issue1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "No access")

    def test_post_issue__comment(self):
        username = self.teacher
        password = self.teacher_password
        issue_data = {
            'status': {
                'color': '#818A91',
                'tag': 'new',
                'id': 1,
                'name': 'New'
            },
            'task': {
                'id': 1,
                'title': 'task_title1'
            },
            'responsible': None,
            'id': 1,
            'followers': [],
            'student': {
                'username': 'student',
                'first_name': 'student_name',
                'last_name': 'student_last_name',
                'middle_name': None,
                'name': 'student_name student_last_name',
                'id': 3
            },
            'mark': 0.0,
            'events': [
                {
                    'files': [
                        {
                            'id': 1,
                            'filename': 'test_fail_rb.py'
                        }
                    ],
                    'message': '<div class="contest-response-comment not-sanitize">Test comment</div>',
                    'id': 1,
                    'author': {
                        'username': 'anytask',
                        'first_name': '',
                        'last_name': '',
                        'middle_name': None,
                        'name': '',
                        'id': 1
                    }
                },
                {
                    'files': [],
                    'message': '<div class="contest-response-comment not-sanitize">Hello from test</div>',
                    'id': 2,
                    'author': {
                        'username': 'teacher',
                        'first_name': 'teacher_name',
                        'last_name': 'teacher_last_name',
                        'middle_name': None,
                        'name': 'teacher_name teacher_last_name',
                        'id': 2
                    }
                }
            ]
        }

        response = self._request(username, password,
                                 path=reverse(api.views.get_or_post_issue, kwargs={"issue_id": self.issue1.id}),
                                 method=self.client.post, data={"comment": "Hello from test"})
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.clean_timestamps(response_data)
        url = response_data['events'][0]['files'][0].pop("url")
        path = response_data['events'][0]['files'][0].pop("path")
        self.assertIn("http", url)
        self.assertIn("/media/", url)
        self.assertIn("/media/", path)
        self.assertDictEqual(issue_data, response_data)

    def test_post_issue__status(self, status=None):
        username = self.teacher
        password = self.teacher_password
        issue_data = {
            'status': {
                'color': '#ACCD8C',
                'tag': 'accepted_after_deadline',
                'id': 7,
                'name': 'Accepted after deadline'
            },
            'task': {
                'id': 1,
                'title': 'task_title1'
            },
            'responsible': None,
            'id': 1,
            'followers': [],
            'student': {
                'username': 'student',
                'first_name': 'student_name',
                'last_name': 'student_last_name',
                'middle_name': None,
                'name': 'student_name student_last_name',
                'id': 3
            },
            'mark': 0.0,
            'events': [
                {
                    'files': [
                        {
                            'id': 1,
                            'filename': 'test_fail_rb.py'
                        }
                    ],
                    'message': '<div class="contest-response-comment not-sanitize">Test comment</div>',
                    'id': 1,
                    'author': {
                        'username': 'anytask',
                        'first_name': '',
                        'last_name': '',
                        'middle_name': None,
                        'name': '',
                        'id': 1
                    }
                },
                {
                    'files': [],
                    'message': 'status_izmenen'
                               ' \u0417\u0430\u0447\u0442\u0435\u043d\u043e \u043f\u043e\u0441\u043b\u0435'
                               ' \u0434\u0435\u0434\u043b\u0430\u0439\u043d\u0430',
                    'id': 2,
                    'author': {
                        'username': 'teacher',
                        'first_name': 'teacher_name',
                        'last_name': 'teacher_last_name',
                        'middle_name': None,
                        'name': 'teacher_name teacher_last_name',
                        'id': 2
                    }
                }
            ]
        }

        if status is None:
            status = self.course.issue_status_system.statuses.all().order_by("-id")[0].id

        response = self._request(username, password,
                                 path=reverse(api.views.get_or_post_issue, kwargs={"issue_id": self.issue1.id}),
                                 method=self.client.post, data={"status": status})
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.clean_timestamps(response_data)
        url = response_data['events'][0]['files'][0].pop("url")
        path = response_data['events'][0]['files'][0].pop("path")
        self.assertIn("http", url)
        self.assertIn("/media/", url)
        self.assertIn("/media/", path)
        self.assertDictEqual(issue_data, response_data)

    def test_post_issue__mark(self):
        username = self.teacher
        password = self.teacher_password
        issue_data = {
            'status': {
                'color': '#818A91',
                'tag': 'new',
                'id': 1,
                'name': 'New'
            },
            'task': {
                'id': 1,
                'title': 'task_title1'
            },
            'responsible': None,
            'id': 1,
            'followers': [],
            'student': {
                'username': 'student',
                'first_name': 'student_name',
                'last_name': 'student_last_name',
                'middle_name': None,
                'name': 'student_name student_last_name',
                'id': 3
            },
            'mark': 2.0,
            'events': [
                {
                    'files': [
                        {
                            'id': 1,
                            'filename': 'test_fail_rb.py'
                        }
                    ],
                    'message': '<div class="contest-response-comment not-sanitize">Test comment</div>',
                    'id': 1,
                    'author': {
                        'username': 'anytask',
                        'first_name': '',
                        'last_name': '',
                        'middle_name': None,
                        'name': '',
                        'id': 1
                    }
                }
            ]
        }

        response = self._request(username, password,
                                 path=reverse(api.views.get_or_post_issue, kwargs={"issue_id": self.issue1.id}),
                                 method=self.client.post, data={"mark": 2.0})
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.clean_timestamps(response_data)
        url = response_data['events'][0]['files'][0].pop("url")
        path = response_data['events'][0]['files'][0].pop("path")
        self.assertIn("http", url)
        self.assertIn("/media/", url)
        self.assertIn("/media/", path)
        self.assertDictEqual(issue_data, response_data)

    def test_post_issue__status_tag(self):
        self.test_post_issue__status(self.course.issue_status_system.statuses.all().order_by("-id")[0].tag)

    def test_post_issue__no_access(self):
        response = self._request(self.anytask, self.anytask_password,
                                 path=reverse(api.views.get_or_post_issue, kwargs={"issue_id": self.issue1.id}),
                                 method=self.client.post, data={"comment": "No access"})
        self.assertEqual(response.status_code, 403)

        status = self.course.issue_status_system.statuses.all().order_by("-id")[0]
        response = self._request(self.anytask, self.anytask_password,
                                 path=reverse(api.views.get_or_post_issue, kwargs={"issue_id": self.issue1.id}),
                                 method=self.client.post, data={"status": status.id})
        self.assertEqual(response.status_code, 403)

        response = self._request(self.anytask, self.anytask_password,
                                 path=reverse(api.views.get_or_post_issue, kwargs={"issue_id": self.issue1.id}),
                                 method=self.client.post, data={"status": status.tag})
        self.assertEqual(response.status_code, 403)

        response = self._request(self.anytask, self.anytask_password,
                                 path=reverse(api.views.get_or_post_issue, kwargs={"issue_id": self.issue1.id}),
                                 method=self.client.post, data={"mark": 2.0})
        self.assertEqual(response.status_code, 403)

        response = self._request(self.teacher, self.teacher_password,
                                 path=reverse(api.views.get_or_post_issue, kwargs={"issue_id": self.issue1.id}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "No access")

    def test_get_issue_statuses(self):
        username = self.teacher
        password = self.teacher_password
        statuses = [
            {
                "color": "#818A91",
                "tag": "new",
                "id": 1,
                "name": "New"
            },
            {
                "color": "#818A91",
                "tag": "auto_verification",
                "id": 2,
                "name": "Auto-checking"
            },
            {
                "color": "#F0AD4E",
                "tag": "verification",
                "id": 3,
                "name": "Checking"
            },
            {
                "color": "#D9534F",
                "tag": "rework",
                "id": 4,
                "name": "Revising"
            },
            {
                "color": "#5CB85C",
                "tag": "accepted",
                "id": 5,
                "name": "Accepted"
            },
            {
                "color": "#5BC0DE",
                "tag": "need_info",
                "id": 6,
                "name": "Need information"
            },
            {
                "color": "#ACCD8C",
                "tag": "accepted_after_deadline",
                "id": 7,
                "name": "Accepted after deadline"
            }
        ]

        response = self._request(username, password,
                                 path=reverse(api.views.get_issue_statuses, kwargs={"course_id": self.course.id}))
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertListEqual(statuses, response_data)

    def test_get_issue_statuses__no_access(self):
        response = self._request(self.anytask, self.anytask_password,
                                 path=reverse(api.views.get_issue_statuses, kwargs={"course_id": self.course.id}))
        self.assertEqual(response.status_code, 403)

        response = self._request(self.teacher, self.teacher_password,
                                 path=reverse(api.views.get_issue_statuses, kwargs={"course_id": self.course.id}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "No access")
