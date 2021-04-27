from flask import Flask
from flask_session import Session

gitlab_mock_app = Flask(__name__)

gitlab_mock_app.config['SECRET_KEY'] = "testing"

from gitlabMock import routes
