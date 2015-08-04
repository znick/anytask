# -*- coding: utf-8 -*-
import requests

import logging
from django.conf import settings

def upload_contest(event, extension, file):
    logger = logging.getLogger('django.request')
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
        sent = True
        logger.info('Contest submission with run_id '+str(run_id)+' sent successfully.')
        issue.set_byname(name='run_id', value=run_id)
    except Exception as e:
        logger.exception(e)
        sent = False
    return sent
