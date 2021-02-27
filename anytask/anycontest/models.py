# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django.contrib.auth.models import User
from anycontest.common import FakeResponse, escape, user_register_to_contest

import requests
import os
import logging
import time

logger = logging.getLogger('django.request')


class ContestSubmissionRunning(Exception):
    pass


class ContestSubmissionWaiting(Exception):
    pass


class ContestSubmission(models.Model):
    issue = models.ForeignKey('issues.Issue', db_index=True, null=False, blank=False)
    author = models.ForeignKey(User, null=False, blank=False)
    file = models.ForeignKey('issues.File', null=False, blank=False)

    run_id = models.CharField(max_length=191, blank=True)
    compiler_id = models.CharField(max_length=191, blank=True)
    send_error = models.TextField(null=True, blank=True)

    got_verdict = models.BooleanField(default=False)
    full_response = models.TextField(null=True, blank=True)
    verdict = models.TextField(null=True, blank=True)
    precompile_checks = models.TextField(null=True, blank=True)
    compile_log = models.TextField(null=True, blank=True)
    used_time = models.IntegerField(null=True, blank=True)
    used_memory = models.IntegerField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    test_number = models.IntegerField(null=True, blank=True)

    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    sended_notify = models.BooleanField(default=False)

    def __str__(self):
        return u"{0} {1}".format(self.issue, self.run_id)

    def upload_contest(self, extension=None, compiler_id=None):
        problem_req = FakeResponse()
        submit_req = FakeResponse()
        reg_req = FakeResponse()
        message = "OK"

        try:
            issue = self.issue
            file = self.file
            student_profile = issue.student.profile
            contest_id = issue.task.contest_id
            course = issue.task.course
            if not compiler_id:
                compiler_id = self.get_compiler_id(extension)

            self.compiler_id = compiler_id[0] if isinstance(compiler_id, list) else compiler_id

            if student_profile.ya_contest_oauth and course.send_to_contest_from_users:
                oauth = student_profile.ya_contest_oauth
                reg_req = requests.get(
                    settings.CONTEST_API_URL + 'status?contestId=' + str(contest_id),
                    headers={'Authorization': 'OAuth ' + oauth})
                if 'error' in reg_req.json():
                    self.send_error = reg_req.json()["error"]["message"]
                    self.save()
                    return False

                if not reg_req.json()['result']['isRegistered']:
                    got_info, response_text = user_register_to_contest(contest_id, student_profile.ya_contest_uid)
                    if not got_info:
                        self.send_error = response_text
                        self.save()
                        return False
            else:
                oauth = settings.CONTEST_OAUTH
            problem_req = requests.get(settings.CONTEST_API_URL + 'problems?contestId=' + str(contest_id),
                                       headers={'Authorization': 'OAuth ' + settings.CONTEST_OAUTH})
            problem_id = None
            for problem in problem_req.json()['result']['problems']:
                if problem['title'] == issue.task.problem_id:
                    problem_id = problem['id']
                    break

            if problem_id is None:
                logger.error("Cant find problem_id '%s' for issue '%s'", issue.task.problem_id, issue.id)
                self.send_error = "Cant find problem '{0}' in Yandex.Contest".format(issue.task.problem_id)
                self.save()
                return False

            for i in range(3):
                with open(os.path.join(settings.MEDIA_ROOT, file.file.name), 'rb') as f:
                    files = {'file': f}
                    submit_req = requests.post(settings.CONTEST_API_URL + 'submit',
                                               data={'compilerId': compiler_id,
                                                     'contestId': contest_id,
                                                     'problemId': problem_id},
                                               files=files,
                                               headers={'Authorization': 'OAuth ' + oauth})
                    if 'error' not in submit_req.json():
                        break
                    time.sleep(0.5)

            if 'error' in submit_req.json():
                self.send_error = submit_req.json()["error"]["message"]
                self.save()
                return False

            run_id = submit_req.json()['result']['value']
            sent = True
            logger.info("Contest submission with run_id '%s' sent successfully.", run_id)
            issue.set_byname(name='run_id', value=run_id)
            self.run_id = run_id
            self.save()
        except Exception as e:
            logger.exception("Exception while request to Contest: '%s' : '%s', '%s' : '%s', Exception: '%s'",
                             problem_req.url, problem_req.json(), submit_req.url, submit_req.json(), e)
            sent = False
            message = "Unexpected error"

        if not sent:
            self.send_error = message
            self.save()

        return sent

    def get_contest_mark(self):
        results_req = FakeResponse()
        run_id = self.run_id
        issue = self.issue

        try:
            oauth = settings.CONTEST_OAUTH
            contest_id = issue.task.contest_id
            results_req = requests.get(
                settings.CONTEST_V1_API_URL + '/contests/' + str(contest_id) + '/submissions/' + str(run_id) + '/full',
                headers={'Authorization': 'OAuth ' + oauth}
            )
            results_req_json = results_req.json()
            issue.set_byname('mark', float(results_req_json['finalScore']))

            logger.info("Contest submission mark with run_id '%s' got successfully.", run_id)
            got_mark = True
        except Exception as e:
            logger.exception("Exception while request to Contest: '%s' : '%s', Exception: '%s'",
                             results_req.url, results_req.json(), e)
            got_mark = False
        self.save()

        return got_mark

    def get_compiler_id(self, extension):
        course_id = self.issue.task.course.id
        compiler_id = settings.CONTEST_EXTENSIONS[extension]
        if course_id not in settings.CONTEST_EXTENSIONS_COURSE:
            return compiler_id

        if extension not in settings.CONTEST_EXTENSIONS_COURSE[course_id]:
            return compiler_id

        return settings.CONTEST_EXTENSIONS_COURSE[course_id][extension]

    def check_submission(self):
        results_req = FakeResponse()
        issue = self.issue
        comment = ''
        run_id = self.run_id

        try:
            student_profile = issue.student.profile
            course = issue.task.course
            if student_profile.ya_contest_oauth and course.send_to_contest_from_users:
                oauth = student_profile.ya_contest_oauth
            else:
                oauth = settings.CONTEST_OAUTH
            contest_id = issue.task.contest_id
            results_req = requests.get(
                settings.CONTEST_API_URL + 'results?runId=' + str(run_id) + '&contestId=' + str(contest_id),
                headers={'Authorization': 'OAuth ' + oauth}
            )
            results_req_json = results_req.json()
            self.full_response = results_req.content

            if results_req_json['result']['submission']['status'] == "waiting":
                raise ContestSubmissionWaiting

            if results_req_json['result']['submission']['status'] == "running":
                raise ContestSubmissionRunning

            contest_verdict = results_req_json['result']['submission']['verdict']
            self.verdict = contest_verdict
            if contest_verdict == 'ok':
                comment = u'<p>{0}: ok</p>'.format(_(u'verdikt_jakontest'))
            elif contest_verdict == 'precompile-check-failed':
                contest_messages = []
                for precompile_check in results_req_json['result']['precompileChecks']:
                    contest_messages.append(precompile_check['message'])
                self.precompile_checks = u'\n'.join(contest_messages)
                comment = u'<p>{0}: precompile-check-failed</p><pre>'.format(_(u'verdikt_jakontest')) + \
                          escape(u'\n'.join(contest_messages)) + \
                          u'</pre>'
            else:
                self.compile_log = results_req_json['result']['compileLog'][18:]
                comment = u'<p>{0}: '.format(_(u'verdikt_jakontest')) \
                          + results_req_json['result']['submission']['verdict'] + '</p><pre>' \
                          + escape(results_req_json['result']['compileLog'][18:]) + '</pre>'
                if results_req_json['result']['tests']:
                    test = results_req_json['result']['tests'][-1]
                    self.used_time = test['usedTime']
                    self.used_memory = test['usedMemory']
                    test_resourses = u'<p><u>{0}</u> '.format(_(u'resursy')) + str(test['usedTime']) \
                                     + 'ms/' + '%.2f' % (test['usedMemory'] / (1024. * 1024)) + 'Mb</p>'
                    if 'input' in test:
                        test_input = u'<p><u>{0}</u></p><pre>'.format(_(u'vvod')) + \
                                     escape(test['input']) if test['input'] else ""
                        test_input += '</pre>'
                    else:
                        test_input = ""
                    if 'output' in test:
                        test_output = u'<p><u>{0}</u></p><pre>'.format(_(u'vyvod_programmy')) + \
                                      escape(test['output']) if test['output'] else ""
                        test_output += '</pre>'
                    else:
                        test_output = ""
                    if 'answer' in test:
                        test_answer = u'<p><u>{0}</u></p><pre>'.format(_(u'pravilnyj_otvet')) + \
                                      escape(test['answer']) if test['answer'] else ""
                        test_answer += '</pre>'
                    else:
                        test_answer = ""
                    if 'error' in test:
                        self.error = test['error']
                        test_error = u'<p><u>Stderr</u></p><pre>' + \
                                     escape(test['error']) if test['error'] else ""
                        test_error += '</pre>'
                    else:
                        test_error = ""
                    if 'message' in test:
                        self.message = test['message']
                        test_message = u'<p><u>{0}</u></p><pre>'.format(_(u'soobshenie_chekera')) + \
                                       escape(test['message']) if test['message'] else ""
                        test_message += '</pre>'
                    else:
                        test_message = ""
                    self.test_number = test['testNumber']
                    comment += u'<p><u>{0} '.format(_(u'test')) + str(test['testNumber']) + '</u>' \
                               + test_resourses + test_input + test_output \
                               + test_answer + test_error + test_message + '</p>'

            logger.info("Contest submission verdict with run_id '%s' got successfully.", run_id)
            got_verdict = True
        except ContestSubmissionWaiting:
            logger.warning("Run_id %s is waiting for %s", run_id, timezone.now() - self.create_time)
            got_verdict = False
        except ContestSubmissionRunning:
            logger.warning("Run_id %s is running for %s", run_id, timezone.now() - self.create_time)
            got_verdict = False
        except Exception as e:
            logger.exception("Exception while request to Contest: '%s' : '%s', Exception: '%s'",
                             results_req.url, results_req.json(), e)
            got_verdict = False

        self.got_verdict = got_verdict
        self.save()

        return comment
