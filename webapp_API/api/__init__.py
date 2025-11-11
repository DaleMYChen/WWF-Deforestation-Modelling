# Blueprint initialization
from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from . import routes  # Import routes after creating the blueprint