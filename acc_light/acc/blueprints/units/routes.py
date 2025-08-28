from flask import render_template
from acc.blueprints.units import bp

@bp.route('/')
def index():
    return render_template('units/index.html')