from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.brokers import bp
from acc.models import Broker, BrokerDue, Contract, Voucher
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination, parse_number, get_today
from sqlalchemy import func

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    # Base query
    query = Broker.query
    
    # Search
    if search:
        query = query.filter(
            db.or_(
                Broker.name.ilike(f'%{search}%'),
                Broker.phone.ilike(f'%{search}%')
            )
        )
    
    # Filter by status
    if status:
        query = query.filter(Broker.status == status)
    
    # Order by name
    query = query.order_by(Broker.name)
    
    # Pagination
    pagination = Pagination(query, page)
    brokers = pagination.items
    
    # Calculate stats
    total_brokers = Broker.query.count()
    active_brokers = Broker.query.filter_by(status='نشط').count()
    
    # Calculate total commissions
    total_commissions = db.session.query(func.sum(Contract.broker_amount)).filter(
        Contract.broker_name.isnot(None)
    ).scalar() or 0
    
    return render_template('brokers/index.html',
                         brokers=brokers,
                         pagination=pagination,
                         search=search,
                         status=status,
                         total_brokers=total_brokers,
                         active_brokers=active_brokers,
                         total_commissions=total_commissions)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        status = request.form.get('status', 'نشط')
        notes = request.form.get('notes', '').strip()
        
        if not name:
            flash('الرجاء إدخال اسم السمسار', 'error')
            return redirect(url_for('brokers.add'))
        
        # Check duplicate
        if Broker.query.filter_by(name=name).first():
            flash('اسم السمسار موجود بالفعل', 'error')
            return redirect(url_for('brokers.add'))
        
        broker = Broker(
            id=generate_uid('BR'),
            name=name,
            phone=phone,
            status=status,
            notes=notes
        )
        
        db.session.add(broker)
        log_action('إضافة سمسار جديد', {'id': broker.id, 'name': broker.name})
        db.session.commit()
        
        flash('تم إضافة السمسار بنجاح', 'success')
        return redirect(url_for('brokers.detail', id=broker.id))
    
    return render_template('brokers/add.html')


@bp.route('/<id>')
def detail(id):
    broker = Broker.query.get_or_404(id)
    
    # Get broker contracts
    contracts = Contract.query.filter_by(broker_name=broker.name).order_by(Contract.created_at.desc()).all()
    
    # Calculate totals
    total_sales = sum(c.total_price or 0 for c in contracts)
    total_commission = sum(c.broker_amount or 0 for c in contracts)
    
    # Get broker dues
    dues = broker.dues.order_by(BrokerDue.created_at.desc()).all()
    total_due = sum(due.remaining_amount for due in dues if due.status == 'نشط')
    
    return render_template('brokers/detail.html',
                         broker=broker,
                         contracts=contracts,
                         total_sales=total_sales,
                         total_commission=total_commission,
                         dues=dues,
                         total_due=total_due,
                         today=get_today())


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    broker = Broker.query.get_or_404(id)
    old_name = broker.name
    
    if request.method == 'POST':
        broker.name = request.form.get('name', '').strip()
        broker.phone = request.form.get('phone', '').strip()
        broker.status = request.form.get('status', 'نشط')
        broker.notes = request.form.get('notes', '').strip()
        
        if not broker.name:
            flash('الرجاء إدخال اسم السمسار', 'error')
            return redirect(url_for('brokers.edit', id=id))
        
        # Check duplicate
        existing = Broker.query.filter_by(name=broker.name).first()
        if existing and existing.id != id:
            flash('اسم السمسار موجود بالفعل', 'error')
            return redirect(url_for('brokers.edit', id=id))
        
        # Update contract broker names if name changed
        if old_name != broker.name:
            Contract.query.filter_by(broker_name=old_name).update({'broker_name': broker.name})
        
        log_action('تعديل سمسار', {'id': broker.id, 'name': broker.name})
        db.session.commit()
        
        flash('تم تحديث بيانات السمسار بنجاح', 'success')
        return redirect(url_for('brokers.detail', id=id))
    
    return render_template('brokers/edit.html', broker=broker)


@bp.route('/<id>/add-due', methods=['POST'])
def add_due(id):
    broker = Broker.query.get_or_404(id)
    
    amount = parse_number(request.form.get('amount', 0))
    description = request.form.get('description', '').strip()
    
    if amount <= 0:
        flash('الرجاء إدخال مبلغ صحيح', 'error')
        return redirect(url_for('brokers.detail', id=id))
    
    due = BrokerDue(
        id=generate_uid('BD'),
        broker_id=id,
        amount=amount,
        remaining_amount=amount,
        description=description,
        status='نشط'
    )
    
    db.session.add(due)
    log_action('إضافة مستحق للسمسار', {
        'broker_id': id,
        'amount': amount
    })
    db.session.commit()
    
    flash('تم إضافة المستحق بنجاح', 'success')
    return redirect(url_for('brokers.detail', id=id))


@bp.route('/<broker_id>/pay-due/<due_id>', methods=['POST'])
def pay_due(broker_id, due_id):
    due = BrokerDue.query.get_or_404(due_id)
    
    if due.broker_id != broker_id:
        flash('خطأ في البيانات', 'error')
        return redirect(url_for('brokers.detail', id=broker_id))
    
    amount = parse_number(request.form.get('amount', 0))
    payment_date = request.form.get('payment_date', get_today().isoformat())
    safe_id = request.form.get('safe_id')
    notes = request.form.get('notes', '')
    
    if amount <= 0 or amount > due.remaining_amount:
        flash('الرجاء إدخال مبلغ صحيح', 'error')
        return redirect(url_for('brokers.detail', id=broker_id))
    
    # Create payment voucher
    voucher = Voucher(
        id=generate_uid('V'),
        type='payment',
        amount=amount,
        date=payment_date,
        safe_id=safe_id,
        entity_type='broker',
        entity_id=broker_id,
        description=f'دفعة لمستحق السمسار - {due.broker.name}',
        notes=notes
    )
    
    db.session.add(voucher)
    
    # Update due
    due.remaining_amount -= amount
    if due.remaining_amount == 0:
        due.status = 'مسدد'
    
    log_action('سداد مستحق سمسار', {
        'due_id': due_id,
        'amount': amount,
        'voucher_id': voucher.id
    })
    
    db.session.commit()
    
    flash('تم تسجيل الدفعة بنجاح', 'success')
    return redirect(url_for('brokers.detail', id=broker_id))


# API endpoints
@bp.route('/api/brokers')
def api_brokers():
    brokers = Broker.query.filter_by(status='نشط').order_by(Broker.name).all()
    return jsonify([{
        'id': b.id,
        'name': b.name,
        'phone': b.phone
    } for b in brokers])