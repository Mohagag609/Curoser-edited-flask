from flask import render_template
from acc.blueprints.brokers import bp

@bp.route('/')
def index():
    return '<h1>brokers - Coming Soon</h1>'
