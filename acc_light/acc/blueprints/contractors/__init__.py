from flask import Blueprint

bp = Blueprint('contractors', __name__, template_folder='templates')

from acc.blueprints.contractors import routes
