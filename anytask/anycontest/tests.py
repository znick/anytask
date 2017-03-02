from django.test import TestCase

from django.contrib.auth.models import User
from schools.models import School
from courses.models import Course, IssueField
from groups.models import Group
from years.models import Year
from tasks.models import Task
from issues.models import Issue, File, Event
from issues.model_issue_status import IssueStatus
from django.conf import settings

from common import get_contest_info
import logging

from django.core.files.uploadedfile import SimpleUploadedFile
from mock import patch
from BeautifulSoup import BeautifulSoup
from datetime import datetime, timedelta
from django.core.urlresolvers import reverse

import threading
import BaseHTTPServer
import SimpleHTTPServer
import SocketServer
import time

logging.basicConfig(level=logging.DEBUG)

class ContestServerMock(threading.Thread):
    class Handler(SimpleHTTPServer.SimpleHTTPRequestHandler):
        pass
        # def do_GET(self):
        #     print self.

    def run(self):
        server_address = ('127.0.0.1', 0)
        self.httpd = SocketServer.TCPServer(server_address, self.Handler)
        self.httpd.allow_reuse_address = True
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()

class AnyContestTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contest = ContestServerMock()
        cls.contest.start()
        time.sleep(0.5)

        cls.contest_port = cls.contest.httpd.server_address[1]

        print cls.contest_port

    @classmethod
    def tearDownClass(cls):
        cls.contest.stop()

    def setUp(self):

        settings.CONTEST_API_URL = 'http://127.0.0.1:{}/anytask/'.format(self.contest_port)
        settings.CONTEST_URL = "http://127.0.0.1:{}/".format(self.contest_port)
        print settings.CONTEST_API_URL
        print settings.CONTEST_URL

        self.year = Year.objects.create(start_year=2016)
        self.group = Group.objects.create(name='name_groups', year=self.year)
        self.course = Course.objects.create(name='course_name',
                                            year=self.year)
        self.course.groups = [self.group]
        self.course.save()

        self.task = Task.objects.create(title='task',
                                        course=self.course)
        self.student = User.objects.create_user(username='student',
                                                password='password')
        self.responsible = User.objects.create_user(username='responsible',
                                                    password='password')
        # self.followers = [User.objects.create_user(username='follower1',
        #                                            password='password')]

        status = IssueStatus.objects.get(tag=Issue.STATUS_ACCEPTED)

        self.issue = Issue()
        self.issue.student = self.student
        self.issue.task = self.task
        # issue.mark = 3
        self.issue.responsible = self.responsible
        self.issue.status_field = status
        self.issue.save()
        # issue.followers = followers
        self.issue.save()
        self.issue_id = self.issue.id

        # issue = Issue.objects.get(id=issue_id)

    def test_contest_info(self):
        get_contest_info(1)

    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
