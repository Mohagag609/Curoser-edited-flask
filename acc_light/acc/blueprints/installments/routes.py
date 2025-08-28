from flask import render_template
from acc.blueprints.installments import bp

@bp.route('/')
def index():
    return '<h1>installments - Coming Soon</h1>'
