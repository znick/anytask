# -*- coding: utf-8 -*-
import requests

from django.conf import settings

def upload_contest(event, extension, file):
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
        files = {'file': open(settings.MEDIA_ROOT+'/'+file.file.name, 'rb')}
        submit_req = requests.post(settings.CONTEST_API_URL+'submit',
                                   data={'compilerId': compiler_id,
                                         'contestId': contest_id,
                                         'problemId': problem_id},
                                   files=files,
                                   headers={'Authorization': 'OAuth '+settings.CONTEST_OAUTH})
        run_id = submit_req.json()['result']['value']
        comment = u"Отправлено на проверку в Я.Контест"
        issue.set_byname(name='run_id', value=run_id)
        if issue.status != issue.STATUS_ACCEPTED:
           issue.status = issue.STATUS_CONTEST_VERIFICATION
    except Exception as e:
        comment = u'Ошибка отправки в Я.Контест'
    return comment
