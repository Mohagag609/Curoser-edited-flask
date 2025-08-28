from flask import render_template, request
from datetime import datetime, timedelta
from sqlalchemy import func
from acc.blueprints.dashboard import bp
from acc.extensions import db
from acc.models import Unit, Contract, Voucher, Installment, Customer, Partner
from acc.services.utils import format_currency


@bp.route('/')
def index():
    # Get filter dates
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Base queries
    contracts_query = Contract.query
    vouchers_query = Voucher.query
    installments_query = Installment.query
    
    # Apply date filters
    if from_date:
        contracts_query = contracts_query.filter(Contract.start_date >= from_date)
        vouchers_query = vouchers_query.filter(Voucher.date >= from_date)
    if to_date:
        contracts_query = contracts_query.filter(Contract.start_date <= to_date)
        vouchers_query = vouchers_query.filter(Voucher.date <= to_date)
    
    # Calculate KPIs
    total_sales = db.session.query(func.sum(Contract.total_price)).scalar() or 0
    
    total_receipts = vouchers_query.filter(Voucher.type == 'receipt')\
        .with_entities(func.sum(Voucher.amount)).scalar() or 0
    
    total_expenses = vouchers_query.filter(Voucher.type == 'payment')\
        .with_entities(func.sum(Voucher.amount)).scalar() or 0
    
    # Calculate total debt
    total_debt = 0
    for unit in Unit.query.all():
        total_debt += unit.calculate_remaining()
    
    # Unit counts
    unit_counts = {
        'total': Unit.query.count(),
        'available': Unit.query.filter_by(status='متاحة').count(),
        'sold': Unit.query.filter_by(status='مباعة').count(),
        'reserved': Unit.query.filter_by(status='محجوزة').count(),
    }
    
    # Upcoming installments
    today = datetime.now().date()
    upcoming_installments = Installment.query\
        .filter(Installment.status != 'مدفوع')\
        .filter(Installment.due_date >= today)\
        .order_by(Installment.due_date)\
        .limit(10)\
        .all()
    
    # Recent transactions
    recent_transactions = vouchers_query\
        .order_by(Voucher.date.desc())\
        .limit(10)\
        .all()
    
    return render_template('dashboard/index.html',
        total_sales=total_sales,
        total_receipts=total_receipts,
        total_expenses=total_expenses,
        total_debt=total_debt,
        unit_counts=unit_counts,
        upcoming_installments=upcoming_installments,
        recent_transactions=recent_transactions,
        from_date=from_date,
        to_date=to_date,
        format_currency=format_currency
    )