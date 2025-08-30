from flask import Blueprint

bp = Blueprint('vouchers', __name__, template_folder='templates')

from acc.blueprints.vouchers import routes
