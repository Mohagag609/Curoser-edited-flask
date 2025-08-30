from flask import Blueprint

bp = Blueprint('materials', __name__, template_folder='templates')

from . import routes
