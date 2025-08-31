from flask import render_template, request, redirect, url_for, flash, g
from acc.blueprints.installments import bp
from acc.models import Installment, Unit, Contract, Voucher
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination, parse_number, get_today
from datetime import datetime
from sqlalchemy import func, or_

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    unit_id = request.args.get('unit_id', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    
    # Base query
    query = Installment.query
    
    # Search
    if search:
        unit_ids = db.session.query(Unit.id).filter(
            or_(
                Unit.code.ilike(f'%{search}%'),
                Unit.name.ilike(f'%{search}%')
            )
        ).subquery()
        query = query.filter(Installment.unit_id.in_(unit_ids))
    
    # Filters
    if status:
        query = query.filter(Installment.status == status)
    
    if unit_id:
        query = query.filter(Installment.unit_id == unit_id)
    
    if from_date:
        query = query.filter(Installment.due_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    
    if to_date:
        query = query.filter(Installment.due_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    
    # Order by due date
    query = query.order_by(Installment.due_date)
    
    # Pagination
    pagination = Pagination(query, page)
    installments = pagination.items
    
    # Get all units for filter (project specific)
    units = Unit.query.filter_by(project_id=g.project.id).order_by(Unit.code).all()
    
    # Calculate stats
    total_installments = Installment.query.count()
    paid_installments = Installment.query.filter_by(status='مدفوع').count()
    overdue_installments = Installment.query.filter(
        Installment.status != 'مدفوع',
        Installment.due_date < get_today()
    ).count()
    total_remaining = db.session.query(func.sum(Installment.amount)).filter(
        Installment.status != 'مدفوع'
    ).scalar() or 0
    
    return render_template('installments/index.html',
                         installments=installments,
                         pagination=pagination,
                         search=search,
                         status=status,
                         unit_id=unit_id,
                         from_date=from_date,
                         to_date=to_date,
                         units=units,
                         total_installments=total_installments,
                         paid_installments=paid_installments,
                         overdue_installments=overdue_installments,
                         total_remaining=total_remaining,
                         today=get_today())

@bp.route('/<id>')
def detail(id):
    installment = Installment.query.get_or_404(id)
    
    # Get related vouchers
    vouchers = Voucher.query.filter_by(
        linked_type='installment',
        linked_ref=id
    ).order_by(Voucher.date.desc()).all()
    
    return render_template('installments/detail.html',
                         installment=installment,
                         vouchers=vouchers,
                         today=get_today())

@bp.route('/<id>/pay', methods=['POST'])
def pay(id):
    installment = Installment.query.get_or_404(id)
    
    if installment.status == 'مدفوع':
        flash('هذا القسط مدفوع بالفعل!', 'warning')
        return redirect(url_for('installments.detail', id=id))
    
    amount = parse_number(request.form.get('amount', 0))
    payment_date = request.form.get('payment_date', get_today().isoformat())
    safe_id = request.form.get('safe_id')
    notes = request.form.get('notes', '')
    
    if amount <= 0:
        flash('الرجاء إدخال مبلغ صحيح', 'error')
        return redirect(url_for('installments.detail', id=id))
    
    if amount > installment.amount:
        flash('المبلغ المدفوع أكبر من قيمة القسط!', 'error')
        return redirect(url_for('installments.detail', id=id))
    
    # Create voucher
    voucher = Voucher(
        type='receipt',
        date=datetime.strptime(payment_date, '%Y-%m-%d').date(),
        amount=amount,
        safe_id=safe_id,
        linked_type='installment',
        linked_ref=id,
        description=f'سداد قسط - {installment.unit.get_display_name()}',
        notes=notes
    )
    db.session.add(voucher)
    
    # Update installment
    installment.amount -= amount
    if installment.amount <= 0:
        installment.status = 'مدفوع'
        installment.payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
    else:
        installment.status = 'مدفوع جزئياً'
    
    log_action('سداد قسط', {
        'installment_id': id,
        'amount': amount,
        'voucher_id': voucher.id
    })
    
    db.session.commit()
    flash('تم تسجيل الدفعة بنجاح', 'success')
    
    return redirect(url_for('installments.detail', id=id))

@bp.route('/<id>/cancel-payment/<voucher_id>', methods=['POST'])
def cancel_payment(id, voucher_id):
    installment = Installment.query.get_or_404(id)
    voucher = Voucher.query.get_or_404(voucher_id)
    
    if voucher.linked_ref != id:
        flash('هذا السند غير مرتبط بهذا القسط', 'error')
        return redirect(url_for('installments.detail', id=id))
    
    # Update installment amount
    installment.amount += voucher.amount
    if installment.amount == installment.original_amount:
        installment.status = 'غير مدفوع'
        installment.payment_date = None
    else:
        installment.status = 'مدفوع جزئياً'
    
    # Delete voucher
    db.session.delete(voucher)
    
    log_action('إلغاء سداد قسط', {
        'installment_id': id,
        'amount': voucher.amount,
        'voucher_id': voucher_id
    })
    
    db.session.commit()
    flash('تم إلغاء الدفعة بنجاح', 'success')
    
    return redirect(url_for('installments.detail', id=id))

@bp.route('/batch-update', methods=['POST'])
def batch_update():
    installment_ids = request.form.getlist('installment_ids')
    action = request.form.get('action')
    
    if not installment_ids:
        flash('الرجاء اختيار قسط واحد على الأقل', 'warning')
        return redirect(url_for('installments.index'))
    
    if action == 'mark_paid':
        # Mark selected installments as paid
        payment_date = request.form.get('payment_date', get_today().isoformat())
        safe_id = request.form.get('safe_id')
        
        for inst_id in installment_ids:
            installment = Installment.query.get(inst_id)
            if installment and installment.status != 'مدفوع':
                # Create voucher
                voucher = Voucher(
                    type='receipt',
                    date=datetime.strptime(payment_date, '%Y-%m-%d').date(),
                    amount=installment.amount,
                    safe_id=safe_id,
                    linked_type='installment',
                    linked_ref=inst_id,
                    description=f'سداد قسط - {installment.unit.get_display_name()}'
                )
                db.session.add(voucher)
                
                # Update installment
                installment.amount = 0
                installment.status = 'مدفوع'
                installment.payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
        
        db.session.commit()
        flash(f'تم تحديث {len(installment_ids)} قسط بنجاح', 'success')
    
    return redirect(url_for('installments.index'))