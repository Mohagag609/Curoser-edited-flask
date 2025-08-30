from flask import Blueprint

bp = Blueprint('brokers', __name__, template_folder='templates')

from acc.blueprints.brokers import routes
