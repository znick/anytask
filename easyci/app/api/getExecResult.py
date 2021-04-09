import os

from flask import request, make_response

from app.api import bp
from app.easyCI.scheduler import GitlabCIScheduler
from app.easyCI.schedule_task import send_message

GITLAB_WEBHOOKS_TOKEN = os.environ.get('GITLAB_WEBHOOKS_TOKEN')


@bp.route('/gitlabci/', methods=['POST'])
def gitlabci():
    gitlab_token_header = request.headers.get("X-Gitlab-Token")
    if gitlab_token_header is None or \
            gitlab_token_header != GITLAB_WEBHOOKS_TOKEN:
        return make_response("Forbidden", 403)

    pipeline_data = request.get_json()
    job_data = pipeline_data['builds'][0]
    job_id = job_data['id']
    status = job_data['status']
    if status != 'success':
        if status == 'failed':
            # something in CI went wrong
            response = make_response()
            response.status_code = 500
            return response
        else:
            response = make_response()
            response.status_code = 204
            return response

    scheduler = GitlabCIScheduler()
    run_log = scheduler.get_job_artifact(job_id)
    send_message(run_log)

    response = make_response()
    response.status_code = 204
    return response

