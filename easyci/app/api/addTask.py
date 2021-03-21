from app.api import bp
from flask import url_for, make_response, request
from app.easyCI.tasksPool import put_to_pool
from flask import current_app
from werkzeug.local import LocalProxy

logger = LocalProxy(lambda: current_app.logger)


@bp.route('/add_task', methods=['POST'])
def add_task():
    logger.info(3)
    data = request.get_json() or {}
    # todo: Check errors
    put_to_pool(data)
    response = make_response()
    response.status_code = 201
    response.headers['Location'] = url_for('api.add_task')
    return response

