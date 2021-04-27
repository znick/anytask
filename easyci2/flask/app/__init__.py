import os
import logging

from flask import Flask
from flask_session import Session

from app.easyCI.schedule_task import setup_configs

def configure_logging():
    # register root logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('werkzeug').setLevel(logging.INFO)


def create_app():
    app = Flask(__name__)

    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev_key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = SECRET_KEY

    Session(app)

    configure_logging()

    with app.app_context():
        setup_configs()
        from app.main import bp as main_bp
        app.register_blueprint(main_bp)

        from app.api import bp as api_bp
        app.register_blueprint(api_bp, url_prefix='/api')

    return app
