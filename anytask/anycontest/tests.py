from django.test import TestCase
from unittest import skip

from django.contrib.auth.models import User
from courses.models import Course, IssueField
from groups.models import Group
from years.models import Year
from tasks.models import Task
from issues.models import Issue, File, Event
from issues.model_issue_status import IssueStatus
from common import get_contest_info
from anycontest.models import ContestSubmission

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import ugettext as _

import threading
import BaseHTTPServer
import SocketServer
import time
import json
import tests_data
import cgi

from django.test.utils import override_settings


CONTEST_PORT = 8079

class ContestServerMock(threading.Thread):
    allow_reuse_address = True
    class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
        allow_reuse_address = True
        def log_message(self, format, *args):
            return

        def do_GET(self):
            if self.path.startswith("/anytask/contest?contestId="):
                self.send_response(200)
                self.end_headers()
                json.dump(tests_data.CONTEST_INFO, self.wfile)
                return

            if self.path.startswith("/anytask/problems?contestId="):
                self.send_response(200)
                self.end_headers()
                json.dump(tests_data.CONTEST_PROBLEMS, self.wfile)
                return

            if self.path == "/anytask/results?runId=1&contestId=0":
                reply = {
                    'result': {
                        'submission': {
                            'verdict': "ok",
                        }
                    }
                }
                self.send_response(200)
                self.end_headers()
                json.dump(reply, self.wfile)
                return

            if self.path == "/anytask/results?runId=2&contestId=0":
                reply = {
                    'result': {
                        'submission': {
                            'verdict': "precompile-check-failed",
                        },
                        'precompileChecks': [
                            {'message': 'precompile-check-failed-1'},
                            {'message': 'precompile-check-failed-2'},
                            {'message': 'precompile-check-failed-3'},
                        ],
                    }
                }
                self.send_response(200)
                self.end_headers()
                json.dump(reply, self.wfile)
                return

            if self.path == "/anytask/results?runId=3&contestId=0":
                reply = {
                    'result': {
                        'submission': {
                            'verdict': "failed",
                        },
                        'compileLog': "compileLog",
                        'tests': [
                            {
                                'usedTime' : 1,
                                'usedMemory': 2000000,
                                'input': "input",
                                'output': "output",
                                'answer': "answer",
                                'error': "error",
                                'message': "message",
                                'testNumber': 4,
                            },
                        ],
                    }
                }
                self.send_response(200)
                self.end_headers()
                json.dump(reply, self.wfile)
                return

            if self.path == "/anytask/results?runId=5&contestId=0":
                reply = {"bad_answer": True}
                self.send_response(200)
                self.end_headers()
                json.dump(reply, self.wfile)
                return

            self.send_response(501)
            self.end_headers()


        def do_POST(self):
            content_type, pdict = cgi.parse_header(self.headers.getheader("content-type"))
            fields = cgi.parse_multipart(self.rfile, pdict)

            if self.path.startswith("/anytask/submit"):
                if "_failed_" in fields["file"][0]:
                    reply = {
                        'error': {
                            'message': "Submit error in fake server!"
                        }
                    }
                else:
                    reply = {
                        'result': {
                            'value': "1",
                        }
                    }

                self.send_response(200)
                self.end_headers()
                json.dump(reply, self.wfile)
                return

            self.send_response(501)
            self.end_headers()


    def run(self):
        server_address = ('127.0.0.1', CONTEST_PORT)
        self.httpd = SocketServer.TCPServer(server_address, self.Handler)
        self.httpd.allow_reuse_address = True
        self.httpd.submit_error = False
        self.httpd.serve_forever()



    def stop(self):
        self.httpd.shutdown()

@override_settings(CONTEST_API_URL='http://127.0.0.1:{}/anytask/'.format(CONTEST_PORT))
@override_settings(CONTEST_URL="http://127.0.0.1:{}/".format(CONTEST_PORT))
@override_settings(CONTEST_EXTENSIONS={"py": "python"})
class AnyContestTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contest = ContestServerMock()
        cls.contest.start()
        time.sleep(0.5)

        cls.contest_port = cls.contest.httpd.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.contest.stop()

    def setUp(self):
        self.year = Year.objects.create(start_year=2016)
        self.group = Group.objects.create(name='name_groups', year=self.year)
        self.course = Course.objects.create(name='course_name',
                                            year=self.year)
        self.course.groups = [self.group]
        self.course.save()

        self.task = Task.objects.create(title='task',
                                        course=self.course,
                                        problem_id="A")
        self.student = User.objects.create_user(username='student',
                                                password='password')
        self.responsible = User.objects.create_user(username='responsible',
                                                    password='password')

        status = IssueStatus.objects.get(tag=Issue.STATUS_ACCEPTED)

        self.issue = Issue()
        self.issue.student = self.student
        self.issue.task = self.task
        self.issue.responsible = self.responsible
        self.issue.status_field = status
        self.issue.save()
        self.issue.save()
        self.issue_id = self.issue.id

    def test_contest_info(self):
        # with override_settings(CONTEST_API_URL='http://127.0.0.1:{}/anytask/'.format(self.contest_port))
        self.assertDictEqual(get_contest_info(1)[1], tests_data.CONTEST_INFO['result'])

    def test_contest_submition_ok(self):
        contest_submition = ContestSubmission()
        contest_submition.issue = self.issue
        contest_submition.author = self.student

        event_create_file = Event.objects.create(issue=self.issue, field=IssueField.objects.get(name='file'))
        f = File.objects.create(file=SimpleUploadedFile('test_rb.py', 'print "hello world!"'), event=event_create_file)
        contest_submition.file = f

        contest_submition.save()

        self.assertTrue(contest_submition.upload_contest("py"))
        self.assertEquals(contest_submition.run_id, "1")

    def test_contest_submition_fail(self):
        contest_submition = ContestSubmission()
        contest_submition.issue = self.issue
        contest_submition.author = self.student

        event_create_file = Event.objects.create(issue=self.issue, field=IssueField.objects.get(name='file'))
        f = File.objects.create(file=SimpleUploadedFile('test_fail_rb.py', 'print "_failed_"'), event=event_create_file)
        contest_submition.file = f

        contest_submition.save()

        self.assertFalse(contest_submition.upload_contest("py"))
        self.assertEquals(contest_submition.send_error, "Submit error in fake server!")

    def test_check_submission_ok(self):
        contest_submition = ContestSubmission()
        contest_submition.issue = self.issue
        contest_submition.author = self.student
        contest_submition.run_id = "1"

        event_create_file = Event.objects.create(issue=self.issue, field=IssueField.objects.get(name='file'))
        f = File.objects.create(file=SimpleUploadedFile('test_fail_rb.py', 'print "_failed_"'), event=event_create_file)
        contest_submition.file = f

        contest_submition.save()

        comment = contest_submition.check_submission()
        self.assertIn(u'<p>{0}: ok</p>'.format(_(u'verdikt_jakontest')), comment)
        self.assertTrue(contest_submition.got_verdict)

    def test_check_submission_precompile_check_failed(self):
        contest_submition = ContestSubmission()
        contest_submition.issue = self.issue
        contest_submition.author = self.student
        contest_submition.run_id = "2"

        event_create_file = Event.objects.create(issue=self.issue, field=IssueField.objects.get(name='file'))
        f = File.objects.create(file=SimpleUploadedFile('test_fail_rb.py', 'print "_failed_"'), event=event_create_file)
        contest_submition.file = f

        contest_submition.save()

        comment = contest_submition.check_submission()
        self.assertIn(u'<p>{0}: precompile-check-failed</p>'.format(_(u'verdikt_jakontest')), comment)
        self.assertTrue(contest_submition.got_verdict)
        self.assertIn('precompile-check-failed-1', comment)
        self.assertIn('precompile-check-failed-2', comment)
        self.assertIn('precompile-check-failed-3', comment)

    def test_check_submission_failed(self):
        contest_submition = ContestSubmission()
        contest_submition.issue = self.issue
        contest_submition.author = self.student
        contest_submition.run_id = "3"

        event_create_file = Event.objects.create(issue=self.issue, field=IssueField.objects.get(name='file'))
        f = File.objects.create(file=SimpleUploadedFile('test_fail_rb.py', 'print "_failed_"'), event=event_create_file)
        contest_submition.file = f

        contest_submition.save()

        comment = contest_submition.check_submission()
        self.assertTrue(contest_submition.got_verdict)
        self.assertIn(u'<p>{0}: failed</p>'.format(_(u'verdikt_jakontest')), comment)
        self.assertIn("1ms/1.91Mb", comment)
        self.assertIn("input", comment)
        self.assertIn("output", comment)
        self.assertIn("answer", comment)
        self.assertIn("error", comment)
        self.assertIn("message", comment)

    @skip("Bad error handling on this case")
    def test_check_submission_bad_answer(self):
        contest_submition = ContestSubmission()
        contest_submition.issue = self.issue
        contest_submition.author = self.student
        contest_submition.run_id = "4"

        event_create_file = Event.objects.create(issue=self.issue, field=IssueField.objects.get(name='file'))
        f = File.objects.create(file=SimpleUploadedFile('test_fail_rb.py', 'print "_failed_"'), event=event_create_file)
        contest_submition.file = f

        contest_submition.save()

        comment = contest_submition.check_submission()  # Contest returns 501 here and no JSON
        self.assertFalse(contest_submition.got_verdict)

    def test_check_submission_wrong_json(self):
        contest_submition = ContestSubmission()
        contest_submition.issue = self.issue
        contest_submition.author = self.student
        contest_submition.run_id = "5"

        event_create_file = Event.objects.create(issue=self.issue, field=IssueField.objects.get(name='file'))
        f = File.objects.create(file=SimpleUploadedFile('test_fail_rb.py', 'print "_failed_"'), event=event_create_file)
        contest_submition.file = f

        contest_submition.save()

        comment = contest_submition.check_submission()
        self.assertFalse(contest_submition.got_verdict)
