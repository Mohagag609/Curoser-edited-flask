from flask import Blueprint

bp = Blueprint('transfers', __name__, template_folder='templates')

from . import routes