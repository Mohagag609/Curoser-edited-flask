from flask import render_template, request, redirect, url_for, flash
from acc.blueprints.vouchers import bp
from acc.models import Voucher, Safe, Customer, Supplier, Contractor, Partner
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination, parse_number, get_today
from datetime import datetime
from sqlalchemy import func, or_

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    voucher_type = request.args.get('type', '')
    safe_id = request.args.get('safe_id', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    
    # Base query
    query = Voucher.query
    
    # Search
    if search:
        query = query.filter(
            or_(
                Voucher.description.ilike(f'%{search}%'),
                Voucher.notes.ilike(f'%{search}%'),
                Voucher.id.ilike(f'%{search}%')
            )
        )
    
    # Filters
    if voucher_type:
        query = query.filter(Voucher.type == voucher_type)
    
    if safe_id:
        query = query.filter(Voucher.safe_id == safe_id)
    
    if from_date:
        query = query.filter(Voucher.date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    
    if to_date:
        query = query.filter(Voucher.date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    
    # Order by date desc
    query = query.order_by(Voucher.date.desc(), Voucher.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page)
    vouchers = pagination.items
    
    # Get safes for filter
    safes = Safe.query.order_by(Safe.name).all()
    
    # Calculate stats
    total_receipts = db.session.query(func.sum(Voucher.amount)).filter_by(type='receipt').scalar() or 0
    total_payments = db.session.query(func.sum(Voucher.amount)).filter_by(type='payment').scalar() or 0
    
    # Today's stats
    today = get_today()
    today_receipts = db.session.query(func.sum(Voucher.amount)).filter(
        Voucher.type == 'receipt',
        Voucher.date == today
    ).scalar() or 0
    today_payments = db.session.query(func.sum(Voucher.amount)).filter(
        Voucher.type == 'payment',
        Voucher.date == today
    ).scalar() or 0
    
    return render_template('vouchers/index.html',
                         vouchers=vouchers,
                         pagination=pagination,
                         search=search,
                         voucher_type=voucher_type,
                         safe_id=safe_id,
                         from_date=from_date,
                         to_date=to_date,
                         safes=safes,
                         total_receipts=total_receipts,
                         total_payments=total_payments,
                         today_receipts=today_receipts,
                         today_payments=today_payments)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        voucher_type = request.form.get('type', 'receipt')
        amount = parse_number(request.form.get('amount', 0))
        date = request.form.get('date', get_today().isoformat())
        safe_id = request.form.get('safe_id')
        entity_type = request.form.get('entity_type', '')
        entity_id = request.form.get('entity_id', '')
        description = request.form.get('description', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not all([amount, safe_id, description]):
            flash('الرجاء إدخال جميع البيانات المطلوبة', 'error')
            return redirect(url_for('vouchers.add'))
        
        if amount <= 0:
            flash('الرجاء إدخال مبلغ صحيح', 'error')
            return redirect(url_for('vouchers.add'))
        
        voucher = Voucher(
            id=generate_uid('V'),
            type=voucher_type,
            amount=amount,
            date=datetime.strptime(date, '%Y-%m-%d').date(),
            safe_id=safe_id,
            entity_type=entity_type if entity_type else None,
            entity_id=entity_id if entity_id else None,
            description=description,
            notes=notes
        )
        
        db.session.add(voucher)
        
        # Update safe balance
        safe = Safe.query.get(safe_id)
        safe.update_balance()
        
        log_action(f'إضافة سند {voucher_type}', {
            'id': voucher.id,
            'amount': amount,
            'safe': safe.name
        })
        
        db.session.commit()
        
        flash('تم إضافة السند بنجاح', 'success')
        return redirect(url_for('vouchers.detail', id=voucher.id))
    
    # Get data for form
    safes = Safe.query.order_by(Safe.is_default.desc(), Safe.name).all()
    customers = Customer.query.order_by(Customer.name).all()
    suppliers = Supplier.query.order_by(Supplier.name).all()
    contractors = Contractor.query.order_by(Contractor.name).all()
    partners = Partner.query.order_by(Partner.name).all()
    
    return render_template('vouchers/add.html',
                         safes=safes,
                         customers=customers,
                         suppliers=suppliers,
                         contractors=contractors,
                         partners=partners,
                         today=get_today())


@bp.route('/<id>')
def detail(id):
    voucher = Voucher.query.get_or_404(id)
    return render_template('vouchers/detail.html', voucher=voucher)


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    voucher = Voucher.query.get_or_404(id)
    
    # Don't allow editing linked vouchers
    if voucher.linked_type:
        flash('لا يمكن تعديل سند مرتبط بعملية أخرى', 'error')
        return redirect(url_for('vouchers.detail', id=id))
    
    if request.method == 'POST':
        old_amount = voucher.amount
        old_type = voucher.type
        old_safe_id = voucher.safe_id
        
        voucher.type = request.form.get('type', 'receipt')
        voucher.amount = parse_number(request.form.get('amount', 0))
        voucher.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        voucher.safe_id = request.form.get('safe_id')
        voucher.entity_type = request.form.get('entity_type', '') or None
        voucher.entity_id = request.form.get('entity_id', '') or None
        voucher.description = request.form.get('description', '').strip()
        voucher.notes = request.form.get('notes', '').strip()
        
        if not all([voucher.amount, voucher.safe_id, voucher.description]):
            flash('الرجاء إدخال جميع البيانات المطلوبة', 'error')
            return redirect(url_for('vouchers.edit', id=id))
        
        if voucher.amount <= 0:
            flash('الرجاء إدخال مبلغ صحيح', 'error')
            return redirect(url_for('vouchers.edit', id=id))
        
        # Update safe balances
        if old_safe_id != voucher.safe_id:
            old_safe = Safe.query.get(old_safe_id)
            old_safe.update_balance()
        
        safe = Safe.query.get(voucher.safe_id)
        safe.update_balance()
        
        log_action('تعديل سند', {
            'id': voucher.id,
            'old_amount': old_amount,
            'new_amount': voucher.amount
        })
        
        db.session.commit()
        
        flash('تم تحديث السند بنجاح', 'success')
        return redirect(url_for('vouchers.detail', id=id))
    
    # Get data for form
    safes = Safe.query.order_by(Safe.is_default.desc(), Safe.name).all()
    customers = Customer.query.order_by(Customer.name).all()
    suppliers = Supplier.query.order_by(Supplier.name).all()
    contractors = Contractor.query.order_by(Contractor.name).all()
    partners = Partner.query.order_by(Partner.name).all()
    
    return render_template('vouchers/edit.html',
                         voucher=voucher,
                         safes=safes,
                         customers=customers,
                         suppliers=suppliers,
                         contractors=contractors,
                         partners=partners)


@bp.route('/<id>/delete', methods=['POST'])
def delete(id):
    voucher = Voucher.query.get_or_404(id)
    
    # Don't allow deleting linked vouchers
    if voucher.linked_type:
        flash('لا يمكن حذف سند مرتبط بعملية أخرى', 'error')
        return redirect(url_for('vouchers.detail', id=id))
    
    safe = voucher.safe
    
    db.session.delete(voucher)
    
    # Update safe balance
    safe.update_balance()
    
    log_action('حذف سند', {
        'id': id,
        'type': voucher.type,
        'amount': voucher.amount
    })
    
    db.session.commit()
    
    flash('تم حذف السند بنجاح', 'success')
    return redirect(url_for('vouchers.index'))


@bp.route('/print/<id>')
def print_voucher(id):
    voucher = Voucher.query.get_or_404(id)
    return render_template('vouchers/print.html', voucher=voucher)