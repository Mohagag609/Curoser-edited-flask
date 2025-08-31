from flask import Blueprint
from acc.decorators import project_required

bp = Blueprint('installments', __name__, template_folder='templates')

# Apply project_required decorator to all routes
@bp.before_request
@project_required
def require_project():
    pass

from acc.blueprints.installments import routes
