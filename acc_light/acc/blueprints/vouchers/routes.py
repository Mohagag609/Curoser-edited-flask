from flask import render_template
from acc.blueprints.vouchers import bp

@bp.route('/')
def index():
    return '<h1>vouchers - Coming Soon</h1>'
