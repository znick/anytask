import os
from flask import session, request, Response
from gitlabMock import gitlab_mock_app

from app.easyCI.scheduler import GITLAB_REPO_ID, GITLAB_TRIGGER_TOKEN


@gitlab_mock_app.route('/')
@gitlab_mock_app.route('/api/v4/projects/{}/ref/master/trigger/pipeline'.format(GITLAB_REPO_ID), methods=['POST'])
def index():
    assert(request.args.get('token', GITLAB_TRIGGER_TOKEN))
    assert(request.args.get('variables[TASK]', 'Test_task'))
    assert(request.args.get('variables[TIMEOUT]', 10800))
    return Response('', 201)