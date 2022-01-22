import os

from datetime import datetime, timedelta

from cachetools import TTLCache

from flask import request, make_response

from app.api import bp
from app.easyCI.scheduler import GitlabCIScheduler
from app.easyCI.schedule_task import send_message
from flask import current_app
from werkzeug.local import LocalProxy

logger = LocalProxy(lambda: current_app.logger)

GITLAB_WEBHOOKS_TOKEN = os.environ.get('GITLAB_WEBHOOKS_TOKEN')
TASK_STATUSES = TTLCache(maxsize=1024, ttl=timedelta(minutes=15), timer=datetime.now)


@bp.route('/gitlabci/', methods=['POST'])
def gitlabci():
    gitlab_token_header = request.headers.get("X-Gitlab-Token")
    if gitlab_token_header is None or \
            gitlab_token_header != GITLAB_WEBHOOKS_TOKEN:
        return make_response("Forbidden", 403)

    # data got via Gitlab Webhooks
    pipeline_data = request.get_json()
    pipeline_id = pipeline_data["object_attributes"]["id"]

    logger.info("Webhook data: %s", pipeline_data)

    # obtain job data
    job_data = pipeline_data['builds'][0]
    # get job status
    job_status = job_data["status"]
    job_id = job_data['id']

    scheduler = GitlabCIScheduler()
    variables = scheduler.get_pipeline_vars(pipeline_id)

    # init structure for message
    ret = dict()

    # set job data
    ret["job_id"] = job_id
    ret["timestamp"] = job_data["created_at"]
    ret["pipeline_url"] = scheduler.get_pipeline(pipeline_id)["web_url"]
    ret["job_status"] = job_data["status"]

    # set task data
    ret["course_id"] = int(variables["COURSE_ID"])
    ret["issue_id"] = int(variables["ISSUE_ID"])

    ret["status"] = None
    ret["retcode"] = None
    ret["is_timeout"] = None
    ret["output"] = None

    if TASK_STATUSES.get(job_id) == job_status:
        response = make_response()
        response.status_code = 200
        return response

    TASK_STATUSES[job_id] = job_status

    response = make_response()
    if job_status == 'success':
        run_log = scheduler.get_job_artifact(job_id)
        print(run_log)
        ret["status"] = run_log["status"]
        ret["retcode"] = run_log["retcode"]
        ret["is_timeout"] = run_log["is_timeout"]
        ret["output"] = run_log["output"]
        send_message(ret)
        response.status_code = 200

    elif job_status == 'pending':
        response.status_code = 200

    elif job_status == 'running':
        send_message(ret)
        response.status_code = 200

    elif job_status == 'failed':
        # something in GitlabCI went wrong
        response = make_response()
        response.set_data("Something wrong with GitlabCI")
        response.status_code = 500
    else:
        # unknown GitlabCI status
        response = make_response()
        response.set_data("Bad GitlabCI status '{}'".format(job_status))
        response.status_code = 500

    return response

