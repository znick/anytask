# -*- coding: utf-8 -*-

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from prometheus_client.parser import text_string_to_metric_families

from anycontest.models import ContestSubmission
from courses.models import Course, IssueField
from groups.models import Group
from issues.model_issue_status import IssueStatus
from issues.models import Issue, File, Event
from tasks.models import Task
from years.models import Year


class MetricsTest(TestCase):
    def setUp(self):
        year = Year.objects.create(start_year=2016)
        group = Group.objects.create(name='name_groups', year=year)
        course = Course.objects.create(name='course_name', year=year)
        course.groups.set([group])
        task = Task.objects.create(title='task', course=course, problem_id="A")
        self.student = User.objects.create_user(username='student', password='password')

        self.issue = Issue()
        self.issue.student = self.student
        self.issue.task = task
        self.issue.status_field = IssueStatus.objects.get(tag=Issue.STATUS_ACCEPTED)
        self.issue.save()

        event = Event.objects.create(issue=self.issue, field=IssueField.objects.get(name='file'))
        self.file = File.objects.create(file=SimpleUploadedFile('test.py', b'print(1)'), event=event)

    def add_submission(self, age, run_id='', send_error=None, got_verdict=False):
        submission = ContestSubmission.objects.create(issue=self.issue, author=self.student, file=self.file,
                                                      run_id=run_id, send_error=send_error, got_verdict=got_verdict)
        # create_time is auto_now_add, so it can only be moved back after the fact
        ContestSubmission.objects.filter(id=submission.id).update(create_time=timezone.now() - age)

    def get_metrics(self):
        response = self.client.get(reverse('metrics.views.metrics'))
        self.assertEqual(response.status_code, 200)
        return {family.name: family for family in text_string_to_metric_families(response.content.decode('utf-8'))}

    def test_contest_submissions_without_verdict(self):
        self.add_submission(timedelta(minutes=1), run_id='1')
        self.add_submission(timedelta(hours=1), run_id='2')
        self.add_submission(timedelta(hours=2), run_id='3')
        self.add_submission(timedelta(days=30), run_id='4')
        self.add_submission(timedelta(days=2), send_error='Submit error')
        self.add_submission(timedelta(minutes=1))
        self.add_submission(timedelta(hours=1), run_id='5', got_verdict=True)

        samples = {(s.labels['state'], s.labels['age']): s.value
                   for s in self.get_metrics()['anytask_contest_submissions_without_verdict'].samples}

        self.assertEqual(len(samples), 12)
        self.assertEqual(samples[('waiting', 'lt_30m')], 1)
        self.assertEqual(samples[('waiting', '30m_1d')], 2)
        self.assertEqual(samples[('waiting', '1d_7d')], 0)
        self.assertEqual(samples[('waiting', 'gt_7d')], 1)
        self.assertEqual(samples[('send_error', '1d_7d')], 1)
        self.assertEqual(samples[('not_sent', 'lt_30m')], 1)
        self.assertEqual(sum(samples.values()), 6)

    def test_django_metrics(self):
        self.client.get('/')
        self.assertIn('django_http_requests_total_by_method', self.get_metrics())
