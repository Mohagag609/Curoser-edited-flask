from flask import Blueprint

bp = Blueprint('units', __name__, template_folder='templates')

from acc.blueprints.units import routes