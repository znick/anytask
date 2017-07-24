# -*- coding: utf-8 -*-
import requests
import logging
import xmltodict
from BeautifulSoup import BeautifulStoneSoup

from django.conf import settings

logger = logging.getLogger('django.request')
HEADERS = {'Authorization': 'OAuth ' + settings.CONTEST_OAUTH}


def prettify_contest_task_text(task_text):
    return task_text \
        .replace('<table', '<table class="table table-sm"') \
        .replace('src="', 'src="https://contest.yandex.ru')


def process_task_text(text):
    return prettify_contest_task_text(text).replace('"', '\\"')


class FakeResponse(object):
    def __init__(self):
        self.url = None

    @staticmethod
    def json():
        return None


def user_register_to_contest(contest_id, ya_contest_uid):
    req = FakeResponse()
    got_info = False
    response_text = ''
    try:
        req = requests.get(
            settings.CONTEST_API_URL + 'register-user?uidToRegister=' + str(ya_contest_uid) +
            '&contestId=' + str(contest_id),
            headers=HEADERS)
        req_json = req.json()
        if 'error' in req_json:
            got_info = False
            response_text = req_json["error"]["message"]
        elif 'result' in req_json:
            got_info = True
            response_text = req_json["result"]
    except Exception as e:
        logger.exception("Exception while request registration to Contest: '%s' : '%s', Exception: '%s'",
                         req.url, req.json(), e)
        got_info = False
        response_text = req.json()

    return got_info, response_text


def get_problem_compilers(problem_id, contest_id):
    contest_req = FakeResponse()
    problem_compilers = []

    try:
        contest_req = requests.get(settings.CONTEST_API_URL + 'contest?contestId=' + str(contest_id),
                                   headers=HEADERS)
        for problem in contest_req.json()['result']['problems']:
            if problem['alias'] == problem_id:
                problem_compilers = problem['compilers']
    except Exception as e:
        logger.exception("Exception while request to Contest: '%s' : '%s', Exception: '%s'",
                         contest_req.url, contest_req.json(), e)

    return problem_compilers


def escape(text):
    symbols = ["&", "'", '"', "<", ">"]
    symbols_escaped = ["&amp;", "&#39;", "&quot;", "&lt;", "&gt;"]

    for i, j in zip(symbols, symbols_escaped):
        text = text.replace(i, j)

    return text


def comment_verdict(issue, verdict, comment):
    issue.add_comment(comment)
    if not issue.is_status_accepted():
        if verdict:
            issue.set_status_verification()
        else:
            issue.set_status_rework()
    issue.save()


def get_contest_mark(contest_id, problem_id, ya_login):
    results_req = FakeResponse()
    contest_mark = None
    user_id = None
    try:
        results_req = requests.get(
            settings.CONTEST_URL + 'action/api/download-log?contestId=' + str(contest_id) + '&snarkKey=spike')
        try:
            contest_dict = xmltodict.parse(results_req.content)

            users = contest_dict['contestLog']['users']['user']

            for user in users:
                if user['@loginName'] == ya_login:
                    user_id = user['@id']
                    break

            submits = contest_dict['contestLog']['events']['submit']
            submits.reverse()

            for submit in submits:
                if submit['@userId'] == user_id and submit['@problemTitle'] == problem_id \
                        and submit['@verdict'] == 'OK':
                    contest_mark = submit['@score']
                    break
        except:
            soup = BeautifulStoneSoup(results_req.content)
            users = soup.contestlog.users.user

            while users:
                if users != '\n':
                    if users['loginname'] == ya_login:
                        user_id = users['id']
                        break
                users = users.next

            submits = soup.contestlog.events.submit

            while submits:
                if submits != '\n' and submits.name != 'testinglog' and 'userid' in submits:
                    if submits['userid'] == user_id and submits['problemtitle'] == problem_id \
                            and submits['verdict'] == 'OK':
                        contest_mark = submits['score']
                        break
                submits = submits.next

    except Exception as e:
        logger.exception("Exception while request to Contest: '%s', Exception: '%s'",
                         results_req.url, e)
    return contest_mark


def get_contest_info(contest_id, lang=None):
    contest_req = FakeResponse()
    contest_api = settings.CONTEST_API_URL + 'contest?contestId={cont_id}&locale={lang}'

    try:
        lang_ = 'ru' if lang is None else lang
        contest_req = requests.get(contest_api.format(lang=lang_, cont_id=str(contest_id)), headers=HEADERS)

        if 'error' in contest_req.json():
            return False, contest_req.json()["error"]["message"]

        contest_info = contest_req.json()['result']

        if lang is None:
            contest_info_en = requests.get(contest_api.format(lang='en', cont_id=str(contest_id)),
                                           headers=HEADERS).json()['result']
            json_str = u'{{"ru": "{0}", "en": "{1}"}}'
            for problem in contest_info['problems']:
                problem_en = (item for item in contest_info_en['problems']
                              if item['problemId'] == problem['problemId']).next()
                problem['problemTitle'] = json_str.format(problem['problemTitle'], problem_en['problemTitle'])
                problem['statement'] = json_str.format(process_task_text(problem['statement']),
                                                       process_task_text(problem_en['statement']))
        got_info = True
    except Exception as e:
        logger.exception("Exception while request to Contest: '%s' : '%s', Exception: '%s'",
                         contest_req.url, contest_req.json(), e)
        contest_info = {}
        got_info = False

    return got_info, contest_info
