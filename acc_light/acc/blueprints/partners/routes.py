from flask import render_template
from acc.blueprints.partners import bp

@bp.route('/')
def index():
    return '<h1>partners - Coming Soon</h1>'
