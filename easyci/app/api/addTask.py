from app.api import bp
from flask import url_for, make_response, request
from app.easyCI.schedule_task import add_to_scheduler, course_exists
from flask import current_app
from werkzeug.local import LocalProxy

logger = LocalProxy(lambda: current_app.logger)


@bp.route('/add_task', methods=['POST'])
def add_task():
    url = url_for('api.add_task')

    data = request.get_json() or {}

    keys = ["course_id", "title", "files"]
    for key in keys:
        if not (key in data):
            response = make_response("No key in json: " + key)
            response.headers['Location'] = url
            response.status_code = 400
            return response

    if not (course_exists(data["course_id"])):
        response = make_response("No such course_id: " + data["course_id"])
        response.headers['Location'] = url
        response.status_code = 400
        return response

    add_to_scheduler(data)
    response = make_response()
    response.headers['Location'] = url
    response.status_code = 202
    return response

