from flask import render_template
from acc.blueprints.suppliers import bp

@bp.route('/')
def index():
    return '<h1>suppliers - Coming Soon</h1>'
