from flask import Blueprint, jsonify, g
from acc.models import Customer
from acc.decorators import login_required

bp = Blueprint('api_customers', __name__)

@bp.route('/active')
@login_required
def active():
    """جلب العملاء النشطين"""
    customers = Customer.query.filter_by(status='نشط').order_by(Customer.name).all()
    
    return jsonify({
        'customers': [{
            'id': c.id,
            'name': c.name,
            'phone': c.phone
        } for c in customers]
    })