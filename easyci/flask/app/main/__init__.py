from flask import Blueprint
import logging

LOG = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

from app.main import routes
