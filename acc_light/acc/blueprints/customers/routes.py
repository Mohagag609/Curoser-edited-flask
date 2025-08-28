from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.customers import bp
from acc.extensions import db
from acc.models import Customer, Contract, Voucher, Installment
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from sqlalchemy import or_, func


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    
    query = Customer.query
    
    if q:
        query = query.filter(
            or_(
                Customer.name.contains(q),
                Customer.phone.contains(q),
                Customer.national_id.contains(q),
                Customer.address.contains(q)
            )
        )
    
    query = query.order_by(Customer.name)
    pagination = Pagination(query, page)
    
    return render_template('customers/index.html', 
                         customers=pagination.items,
                         pagination=pagination,
                         q=q)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        national_id = request.form.get('national_id', '').strip()
        address = request.form.get('address', '').strip()
        status = request.form.get('status', 'نشط')
        notes = request.form.get('notes', '').strip()
        
        if not name or not phone:
            flash('الرجاء إدخال الاسم ورقم الهاتف على الأقل.', 'error')
            return redirect(url_for('customers.add'))
        
        # Check if customer with same name exists
        existing = Customer.query.filter_by(name=name).first()
        if existing:
            flash('عميل بنفس الاسم موجود بالفعل.', 'error')
            return redirect(url_for('customers.add'))
        
        customer = Customer(
            id=generate_uid('C'),
            name=name,
            phone=phone,
            national_id=national_id,
            address=address,
            status=status,
            notes=notes
        )
        
        db.session.add(customer)
        log_action('إضافة عميل جديد', {'id': customer.id, 'name': customer.name})
        db.session.commit()
        
        flash('تم إضافة العميل بنجاح.', 'success')
        return redirect(url_for('customers.index'))
    
    return render_template('customers/add.html')


@bp.route('/<string:id>')
def detail(id):
    customer = Customer.query.get_or_404(id)
    
    # Get customer contracts
    contracts = Contract.query.filter_by(customer_id=id).all()
    
    # Calculate financial summary
    total_value = sum(c.total_price for c in contracts)
    
    # Get all payments for this customer
    total_paid = 0
    for contract in contracts:
        # Get installment IDs for this contract
        installment_ids = [i.id for i in Installment.query.filter_by(unit_id=contract.unit_id).all()]
        
        # Get vouchers
        voucher_query = db.session.query(func.sum(Voucher.amount)).filter(
            Voucher.type == 'receipt'
        )
        
        if installment_ids:
            voucher_query = voucher_query.filter(
                or_(
                    Voucher.linked_ref == contract.id,
                    Voucher.linked_ref.in_(installment_ids)
                )
            )
        else:
            voucher_query = voucher_query.filter(Voucher.linked_ref == contract.id)
            
        paid = voucher_query.scalar() or 0
        
        total_paid += paid
    
    total_debt = total_value - total_paid
    
    return render_template('customers/detail.html',
                         customer=customer,
                         contracts=contracts,
                         total_value=total_value,
                         total_paid=total_paid,
                         total_debt=total_debt,
                         format_currency=format_currency)


@bp.route('/<string:id>/edit', methods=['GET', 'POST'])
def edit(id):
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        customer.name = request.form.get('name', '').strip()
        customer.phone = request.form.get('phone', '').strip()
        customer.national_id = request.form.get('national_id', '').strip()
        customer.address = request.form.get('address', '').strip()
        customer.status = request.form.get('status', 'نشط')
        customer.notes = request.form.get('notes', '').strip()
        
        if not customer.name or not customer.phone:
            flash('الرجاء إدخال الاسم ورقم الهاتف على الأقل.', 'error')
            return redirect(url_for('customers.edit', id=id))
        
        log_action('تعديل بيانات عميل', {'id': customer.id, 'name': customer.name})
        db.session.commit()
        
        flash('تم تحديث بيانات العميل بنجاح.', 'success')
        return redirect(url_for('customers.detail', id=id))
    
    return render_template('customers/edit.html', customer=customer)


@bp.route('/<string:id>/delete', methods=['POST'])
def delete(id):
    customer = Customer.query.get_or_404(id)
    
    # Check if customer has contracts
    if customer.contracts.count() > 0:
        flash('لا يمكن حذف هذا العميل لأنه مرتبط بعقود.', 'error')
        return redirect(url_for('customers.index'))
    
    log_action('حذف عميل', {'id': customer.id, 'name': customer.name})
    db.session.delete(customer)
    db.session.commit()
    
    flash('تم حذف العميل بنجاح.', 'success')
    return redirect(url_for('customers.index'))


@bp.route('/search')
def search():
    """HTMX endpoint for live search"""
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    query = Customer.query
    
    if q:
        query = query.filter(
            or_(
                Customer.name.contains(q),
                Customer.phone.contains(q),
                Customer.national_id.contains(q)
            )
        )
    
    query = query.order_by(Customer.name)
    pagination = Pagination(query, page)
    
    return render_template('customers/_table.html',
                         customers=pagination.items,
                         pagination=pagination)