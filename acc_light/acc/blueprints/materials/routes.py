from flask import render_template
from acc.blueprints.materials import bp

@bp.route('/')
def index():
    return '<h1>materials - Coming Soon</h1>'
