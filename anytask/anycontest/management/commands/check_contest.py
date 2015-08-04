# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User

from issues.models import Event, Issue
from issues.model_issue_field import IssueField
import requests

class Command(BaseCommand):
    help = "Check contest submissions"

    def handle(self, **options):
        for issue in Issue.objects.filter(status=Issue.STATUS_AUTO_VERIFICATION):
            for event in issue.event_set.all():
                if event.issue.get_byname('run_id') != '':
                    issue = event.issue
                    run_id = issue.get_byname('run_id')
                    contest_id = issue.task.contest_id
                    results_req = requests.get(settings.CONTEST_API_URL+'results?runId='+str(run_id)+'&contestId='+str(contest_id),
                                               headers={'Authorization': 'OAuth '+settings.CONTEST_OAUTH})

                    if results_req.json()['result']['submission']['verdict'] == 'ok':
                        comment = u'Вердикт Я.Контест: ok'
                    else:
                        comment = u'Вердикт Я.Контест: ' \
                                + results_req.json()['result']['submission']['verdict'] + '\n' \
                                + results_req.json()['result']['compileLog'][18:]
                    author, author_get = User.objects.get_or_create(username=issue.student.username)
                    field, field_get = IssueField.objects.get_or_create(name='comment')
                    event = issue.create_event(field, author=author)
                    event.value = comment
                    event.save()
                    if issue.status != issue.STATUS_ACCEPTED:
                        issue.status = issue.STATUS_VERIFICATION
                    event.issue.set_byname('run_id', '')
                    issue.save()
