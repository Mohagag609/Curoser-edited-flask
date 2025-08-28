from flask import render_template
from acc.blueprints.treasury import bp

@bp.route('/')
def index():
    return '<h1>treasury - Coming Soon</h1>'
