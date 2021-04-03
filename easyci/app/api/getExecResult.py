import os

from flask import request, make_response

from app.api import bp
from app.easyCI.schedule_task import send_message

GITLAB_WEBHOOKS_TOKEN = os.environ.get('GITLAB_WEBHOOKS_TOKEN')


@bp.route('/gitlabci/', methods=['POST'])
def gitlabci():
    gitlab_token_header = request.headers.get("X-Gitlab-Token")
    if gitlab_token_header is None or \
            gitlab_token_header != GITLAB_WEBHOOKS_TOKEN:
        return make_response("Forbidden", 403)

    data = request.get_json()
    send_message(data)

    response = make_response()
    response.status_code = 204
    return response


