from flask import render_template
from acc.blueprints.projects import bp

@bp.route('/')
def index():
    return '<h1>projects - Coming Soon</h1>'
