from flask import render_template
from acc.blueprints.system import bp

@bp.route('/')
def index():
    return '<h1>system - Coming Soon</h1>'
