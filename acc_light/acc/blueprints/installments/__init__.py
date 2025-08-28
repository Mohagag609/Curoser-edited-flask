from flask import Blueprint

bp = Blueprint('installments', __name__, template_folder='templates')

from acc.blueprints.installments import routes
