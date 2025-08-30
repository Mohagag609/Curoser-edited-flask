from flask import Blueprint

bp = Blueprint('partners', __name__, template_folder='templates')

from acc.blueprints.partners import routes
