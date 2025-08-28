from flask import render_template
from acc.blueprints.contractors import bp

@bp.route('/')
def index():
    return '<h1>contractors - Coming Soon</h1>'
