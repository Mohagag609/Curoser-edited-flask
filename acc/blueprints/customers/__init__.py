from flask import Blueprint

bp = Blueprint('customers', __name__, template_folder='templates')

from acc.blueprints.customers import routes