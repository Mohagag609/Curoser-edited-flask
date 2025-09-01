from flask import Blueprint, jsonify, g
from acc.models import Unit
from acc.decorators import login_required, project_required

bp = Blueprint('api_units', __name__)

@bp.route('/available')
@login_required
@project_required
def available():
    """جلب الوحدات المتاحة"""
    units = Unit.query.filter_by(
        project_id=g.project.id,
        status='متاحة'
    ).order_by(Unit.code).all()
    
    return jsonify({
        'units': [{
            'id': u.id,
            'code': u.code,
            'name': u.name,
            'building': u.building,
            'floor': u.floor,
            'total_price': float(u.total_price)
        } for u in units]
    })