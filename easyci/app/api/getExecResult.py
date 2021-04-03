import os

from flask import request, make_response

from app.api import bp
from app.easyCI.schedule_task import send_message

GITLAB_TOKEN = os.environ.get('GITLAB_TOKEN')


@bp.route('/gitlabci/', methods=['POST'])
def gitlabci():
    gitlab_token_header = request.headers.get("X-Gitlab-Token")
    if gitlab_token_header is None or gitlab_token_header != GITLAB_TOKEN:
        return make_response("Forbidden", 403)

    data = request.get_json()
    print(data)
    send_message(data)

    response = make_response()
    response.status_code = 204
    return response


