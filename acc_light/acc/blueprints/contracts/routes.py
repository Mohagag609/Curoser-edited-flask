from flask import render_template
from acc.blueprints.contracts import bp

@bp.route('/')
def index():
    return '<h1>contracts - Coming Soon</h1>'
