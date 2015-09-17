# -*- coding: utf-8 -*-
import requests
import logging
import os

from django.conf import settings
from issues.model_issue_field import IssueField
from django.contrib.auth.models import User

logger = logging.getLogger('django.request')

class FakeResponse(object):
    def __init__(self):
        self.url = None

    @staticmethod
    def json():
        return None

def upload_contest(event, extension, file):
    problem_req = FakeResponse()
    submit_req = FakeResponse()
    message = "OK"

    try:
        issue = event.issue
        contest_id = issue.task.contest_id
        compiler_id = settings.CONTEST_EXTENSIONS[extension]
        problem_req = requests.get(settings.CONTEST_API_URL+'problems?contestId='+str(contest_id),
                                   headers={'Authorization': 'OAuth '+settings.CONTEST_OAUTH})
        for problem in problem_req.json()['result']['problems']:
            if problem['title'] == issue.task.problem_id:
                problem_id = problem['id']
                break
        with open(os.path.join(settings.MEDIA_ROOT, file.file.name), 'rb') as f:
            files = {'file': f}
            submit_req = requests.post(settings.CONTEST_API_URL+'submit',
                                       data={'compilerId': compiler_id,
                                             'contestId': contest_id,
                                             'problemId': problem_id},
                                       files=files,
                                       headers={'Authorization': 'OAuth '+settings.CONTEST_OAUTH})

            if 'error' in submit_req.json():
                return False, submit_req.json()["error"]["message"]


            run_id = submit_req.json()['result']['value']
            sent = True
            logger.info('Contest submission with run_id '+str(run_id)+' sent successfully.')
            issue.set_byname(name='run_id', value=run_id)
    except Exception as e:
        logger.exception("Exception while request to Contest: '%s' : '%s', '%s' : '%s', Exception: '%s'",
                         problem_req.url, problem_req.json(), submit_req.url, submit_req.json(), e)
        sent = False
        message = "Unexpected error"
    return sent, message

def check_submission(issue):
    results_req = FakeResponse()
    verdict = False
    comment = ''
    try:
        run_id = issue.get_byname('run_id')
        contest_id = issue.task.contest_id
        results_req = requests.get(settings.CONTEST_API_URL+'results?runId='+str(run_id)+'&contestId='+str(contest_id),
                                   headers={'Authorization': 'OAuth '+settings.CONTEST_OAUTH})

        contest_verdict = results_req.json()['result']['submission']['verdict']
        if contest_verdict == 'ok':
            comment = u'Вердикт Я.Контест: ok'
            verdict = True
        elif contest_verdict == 'precompile-check-failed':
            contest_messages = []
            for precompile_check in results_req.json()['result']['precompileChecks']:
                contest_messages.append(precompile_check['message'])
            comment = u'Вердикт Я.Контест: precompile-check-failed\n' + u'\n'.join(contest_messages)
        else:
            comment = u'Вердикт Я.Контест: ' \
            + results_req.json()['result']['submission']['verdict'] + '\n' \
            + results_req.json()['result']['compileLog'][18:]
        logger.info('Contest submission verdict with run_id '+str(run_id)+' got successfully.')
        got_verdict = True
    except Exception as e:
        logger.exception("Exception while request to Contest: '%s' : '%s', Exception: '%s'",
                         results_req.url, results_req.json(), e)
        got_verdict = False
    return got_verdict, verdict, comment

def comment_verdict(issue, verdict, comment):
    author, author_get = User.objects.get_or_create(username=issue.student.username)
    field, field_get = IssueField.objects.get_or_create(name='comment')
    event = issue.create_event(field, author=author)
    event.value = comment
    event.save()
    if issue.status != issue.STATUS_ACCEPTED:
        if verdict:
            issue.status = issue.STATUS_VERIFICATION
        else:
            issue.status = issue.STATUS_REWORK
    issue.save()
