from flask import Blueprint

bp = Blueprint('system', __name__, template_folder='templates')

from acc.blueprints.system import routes
