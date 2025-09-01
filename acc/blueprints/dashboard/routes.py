from flask import render_template, request
from datetime import datetime, timedelta
from sqlalchemy import func
from acc.blueprints.dashboard import bp
from acc.extensions import db
from acc.models import Unit, Contract, Voucher, Installment, Customer, Partner
from acc.services.utils import format_currency
from acc.services.project_selection import project_required, get_current_project
from acc.services.project_context import filter_by_project

@bp.route('/')
@project_required
def index():
    # Clean up any failed transactions
    try:
        db.session.rollback()
    except:
        pass
    
    # Get filter dates
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Get current project
    current_project = get_current_project()
    
    # Base queries - filter by current project
    contracts_query = filter_by_project(Contract.query, Contract)
    vouchers_query = filter_by_project(Voucher.query, Voucher)
    installments_query = filter_by_project(Installment.query, Installment)
    
    # Apply date filters
    if from_date:
        contracts_query = contracts_query.filter(Contract.start_date >= from_date)
        vouchers_query = vouchers_query.filter(Voucher.date >= from_date)
    if to_date:
        contracts_query = contracts_query.filter(Contract.start_date <= to_date)
        vouchers_query = vouchers_query.filter(Voucher.date <= to_date)
    
    # Calculate KPIs
    total_sales = contracts_query.with_entities(func.sum(Contract.total_price)).scalar() or 0
    
    total_receipts = vouchers_query.filter(Voucher.type == 'receipt')\
        .with_entities(func.sum(Voucher.amount)).scalar() or 0
    
    total_expenses = vouchers_query.filter(Voucher.type == 'payment')\
        .with_entities(func.sum(Voucher.amount)).scalar() or 0
    
    # Calculate total debt
    total_debt = 0
    units_with_contracts = filter_by_project(Unit.query, Unit).all()
    for unit in units_with_contracts:
        try:
            remaining = unit.calculate_remaining()
            total_debt += remaining
        except Exception as e:
            # Skip units that cause errors
            continue
    
    # Unit counts
    # Unit stats - filter by current project
    units_query = filter_by_project(Unit.query, Unit)
    try:
        unit_counts = {
            'total': units_query.count(),
            'available': units_query.filter_by(status='متاحة').count(),
            'sold': units_query.filter_by(status='مباعة').count(),
            'reserved': units_query.filter_by(status='محجوزة').count(),
        }
    except Exception as e:
        # Rollback and retry
        db.session.rollback()
        unit_counts = {
            'total': 0,
            'available': 0,
            'sold': 0,
            'reserved': 0,
        }
    
    # Upcoming installments
    today = datetime.now().date()
    try:
        upcoming_installments = installments_query\
            .filter(Installment.status != 'مدفوع')\
            .filter(Installment.due_date >= today)\
            .order_by(Installment.due_date)\
            .limit(10)\
            .all()
    except:
        db.session.rollback()
        upcoming_installments = []
    
    # Recent transactions
    try:
        recent_transactions = vouchers_query\
            .order_by(Voucher.date.desc())\
            .limit(10)\
            .all()
    except:
        db.session.rollback()
        recent_transactions = []
    
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