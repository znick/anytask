from json import JSONDecoder
from flask import request

from app.main import bp

@bp.route('/')
@bp.route('/index')
def index():
    return "This is EasyCI"

@bp.route('/easyci', methods=['POST'])
def easyci():
    print(JSONDecoder().decode(request.data.decode()))
    return request.data
