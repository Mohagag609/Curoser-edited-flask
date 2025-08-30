from flask import Blueprint

bp = Blueprint('treasury', __name__, template_folder='templates')

from acc.blueprints.treasury import routes
