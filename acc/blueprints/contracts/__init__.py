from flask import Blueprint, request, make_response
from acc.decorators import project_required

bp = Blueprint('contracts', __name__, template_folder='templates')

# Apply project_required decorator to all routes
@bp.before_request
@project_required
def require_project():
    pass

# Handle OPTIONS requests for CORS
@bp.after_request
def after_request(response):
    # Allow AJAX requests from same origin
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'
    return response

from acc.blueprints.contracts import routes
