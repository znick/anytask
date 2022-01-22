import json
from app.api import bp
from app.easyCI.scheduler import GitlabCIScheduler
from flask import current_app, url_for, make_response, request
from werkzeug.local import LocalProxy

logger = LocalProxy(lambda: current_app.logger)


@bp.route('/dashboard/', methods=['GET'])
def dashboard():
    url = url_for('api.dashboard')

    scheduler = GitlabCIScheduler()
    data = scheduler.get_pipelines()

    if not data:
        response = make_response()
        response.headers['Location'] = url
        response.status_code = 204
        return response

    info = []
    for (i, pipeline) in enumerate(data):
        if i > 10:
            break

        if i == 0:
            pipeline_id = pipeline["id"]
            pipeline_vars = scheduler.get_pipeline_vars(pipeline_id)
            print(pipeline_id, pipeline_vars)

        info.append({
            "id" : pipeline["id"],
            "status" : pipeline["status"],
            "created_at": pipeline["created_at"],
            "updated_at": pipeline["updated_at"]
        })

    return json.dumps(info), 200, {'Content-Type': 'text/json'}
