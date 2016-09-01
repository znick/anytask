# -*- coding: utf-8 -*-
import requests
import logging
import os
import xmltodict

from time import sleep
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


def get_compiler_id(course, extension):
    compiler_id = settings.CONTEST_EXTENSIONS[extension]
    if course.id not in settings.CONTEST_EXTENSIONS_COURSE:
        return compiler_id

    if extension not in settings.CONTEST_EXTENSIONS_COURSE[course.id]:
        return compiler_id

    return settings.CONTEST_EXTENSIONS_COURSE[course.id][extension]


def get_problem_compilers(problem_id, contest_id):
    contest_req = FakeResponse()
    problem_compilers = []

    try:
        contest_req = requests.get(settings.CONTEST_API_URL + 'contest?contestId=' + str(contest_id),
                                   headers={'Authorization': 'OAuth ' + settings.CONTEST_OAUTH})
        for problem in contest_req.json()['result']['problems']:
            if problem['alias'] == problem_id:
                problem_compilers = problem['compilers']
    except Exception as e:
        logger.exception("Exception while request to Contest: '%s' : '%s', Exception: '%s'",
                         contest_req.url, contest_req.json(), e)

    return problem_compilers


def upload_contest(event, extension, file, compiler_id=None):
    problem_req = FakeResponse()
    submit_req = FakeResponse()
    reg_req = FakeResponse()
    message = "OK"

    try:
        issue = event.issue
        student_profile = issue.student.get_profile()
        contest_id = issue.task.contest_id
        course = event.issue.task.course
        if not compiler_id:
            compiler_id = get_compiler_id(course, extension)

        if student_profile.ya_contest_oauth and course.send_to_contest_from_users:
            OAUTH = student_profile.ya_contest_oauth
            reg_req = requests.get(
                settings.CONTEST_API_URL + 'status?contestId=' + str(contest_id),
                headers={'Authorization': 'OAuth ' + OAUTH})
            if not reg_req.json()['result']['isRegistered']:
                reg_req = requests.get(
                    settings.CONTEST_API_URL + 'register-user?uidToRegister=' + str(student_profile.ya_uid) +
                    '&contestId=' + str(contest_id),
                    headers={'Authorization': 'OAuth ' + settings.CONTEST_OAUTH})
            if 'error' in reg_req.json():
                return False, reg_req.json()["error"]["message"]
        else:
            OAUTH = settings.CONTEST_OAUTH

        problem_req = requests.get(settings.CONTEST_API_URL + 'problems?contestId=' + str(contest_id),
                                   headers={'Authorization': 'OAuth ' + settings.CONTEST_OAUTH})
        problem_id = None
        for problem in problem_req.json()['result']['problems']:
            if problem['title'] == issue.task.problem_id:
                problem_id = problem['id']
                break

        if problem_id is None:
            logger.error("Cant find problem_id '%s' for issue '%s'", issue.task.problem_id, issue.id)
            return False, "Cant find problem '{0}' in Yandex.Contest".format(issue.task.problem_id)

        for i in range(3):
            with open(os.path.join(settings.MEDIA_ROOT, file.file.name), 'rb') as f:
                files = {'file': f}
                submit_req = requests.post(settings.CONTEST_API_URL + 'submit',
                                           data={'compilerId': compiler_id,
                                                 'contestId': contest_id,
                                                 'problemId': problem_id},
                                           files=files,
                                           headers={'Authorization': 'OAuth ' + OAUTH})
                if not 'error' in submit_req.json():
                    break
                sleep(0.5)

        if 'error' in submit_req.json():
            return False, submit_req.json()["error"]["message"]

        run_id = submit_req.json()['result']['value']
        sent = True
        logger.info("Contest submission with run_id '%s' sent successfully.", run_id)
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
        results_req = requests.get(
            settings.CONTEST_API_URL + 'results?runId=' + str(run_id) + '&contestId=' + str(contest_id),
            headers={'Authorization': 'OAuth ' + settings.CONTEST_OAUTH})

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
        logger.info("Contest submission verdict with run_id '%s' got successfully.", run_id)
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
    if issue.status_field.tag != issue.STATUS_ACCEPTED:
        if verdict:
            issue.set_status_by_tag(issue.STATUS_VERIFICATION)
        else:
            issue.set_status_by_tag(issue.STATUS_REWORK)
    issue.save()


def get_contest_mark(contest_id, problem_id, ya_login):
    results_req = FakeResponse()
    contest_mark = None
    try:
        results_req = requests.get(
           'https://contest.yandex.ru/action/api/download-log?contestId=' + str(contest_id) + '&snarkKey=spike')
        contest_dict = xmltodict.parse(results_req.content)

        users = contest_dict['contestLog']['users']['user']

        user_id = None
        for user in users:
            if user['@loginName'] == ya_login:
                user_id = user['@id']
                break

        submits = contest_dict['contestLog']['events']['submit']
        submits.reverse()

        for submit in submits:
            if submit['@userId'] == user_id and submit['@problemTitle'] == problem_id and submit['@verdict'] == 'OK':
                contest_mark = submit['@score']
                break

    except Exception as e:
        logger.exception("Exception while request to Contest: '%s' : '%s', Exception: '%s'",
                             results_req.url, results_req.json(), e)
    return contest_mark


def get_contest_info(contest_id):
    contest_req = FakeResponse()

    try:
        contest_req = requests.get(settings.CONTEST_API_URL + 'contest?contestId=' + str(contest_id),
                                   headers={'Authorization': 'OAuth ' + settings.CONTEST_OAUTH})

        if 'error' in contest_req.json():
            return False, contest_req.json()["error"]["message"]

        contest_info = contest_req.json()['result']
        got_info = True
    except Exception as e:
        logger.exception("Exception while request to Contest: '%s' : '%s', Exception: '%s'",
                         contest_req.url, contest_req.json(), e)
        contest_info = {}
        got_info = False

    return got_info, contest_info
