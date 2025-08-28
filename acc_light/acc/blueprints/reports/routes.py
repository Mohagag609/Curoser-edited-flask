from flask import render_template
from acc.blueprints.reports import bp

@bp.route('/')
def index():
    return '<h1>reports - Coming Soon</h1>'
