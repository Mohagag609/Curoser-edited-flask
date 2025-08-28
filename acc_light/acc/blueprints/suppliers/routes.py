from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.suppliers import bp
from acc.models import Supplier, Voucher
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination
from sqlalchemy import func

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Base query
    query = Supplier.query
    
    # Search
    if search:
        query = query.filter(
            db.or_(
                Supplier.name.ilike(f'%{search}%'),
                Supplier.phone.ilike(f'%{search}%'),
                Supplier.email.ilike(f'%{search}%')
            )
        )
    
    # Order by name
    query = query.order_by(Supplier.name)
    
    # Pagination
    pagination = Pagination(query, page)
    suppliers = pagination.items
    
    # Calculate stats
    total_suppliers = Supplier.query.count()
    
    # Calculate total payments to suppliers
    total_payments = db.session.query(func.sum(Voucher.amount)).filter(
        Voucher.entity_type == 'supplier',
        Voucher.type == 'payment'
    ).scalar() or 0
    
    return render_template('suppliers/index.html',
                         suppliers=suppliers,
                         pagination=pagination,
                         search=search,
                         total_suppliers=total_suppliers,
                         total_payments=total_payments)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        tax_number = request.form.get('tax_number', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not name:
            flash('الرجاء إدخال اسم المورد', 'error')
            return redirect(url_for('suppliers.add'))
        
        # Check duplicate
        if Supplier.query.filter_by(name=name).first():
            flash('اسم المورد موجود بالفعل', 'error')
            return redirect(url_for('suppliers.add'))
        
        supplier = Supplier(
            id=generate_uid('SP'),
            name=name,
            phone=phone,
            email=email,
            address=address,
            tax_number=tax_number,
            notes=notes
        )
        
        db.session.add(supplier)
        log_action('إضافة مورد جديد', {'id': supplier.id, 'name': supplier.name})
        db.session.commit()
        
        flash('تم إضافة المورد بنجاح', 'success')
        return redirect(url_for('suppliers.detail', id=supplier.id))
    
    return render_template('suppliers/add.html')


@bp.route('/<id>')
def detail(id):
    supplier = Supplier.query.get_or_404(id)
    
    # Get supplier vouchers
    vouchers = Voucher.query.filter_by(
        entity_type='supplier',
        entity_id=id
    ).order_by(Voucher.date.desc()).all()
    
    # Calculate totals
    total_payments = sum(v.amount for v in vouchers if v.type == 'payment')
    total_receipts = sum(v.amount for v in vouchers if v.type == 'receipt')
    balance = total_receipts - total_payments
    
    return render_template('suppliers/detail.html',
                         supplier=supplier,
                         vouchers=vouchers,
                         total_payments=total_payments,
                         total_receipts=total_receipts,
                         balance=balance)


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    supplier = Supplier.query.get_or_404(id)
    
    if request.method == 'POST':
        supplier.name = request.form.get('name', '').strip()
        supplier.phone = request.form.get('phone', '').strip()
        supplier.email = request.form.get('email', '').strip()
        supplier.address = request.form.get('address', '').strip()
        supplier.tax_number = request.form.get('tax_number', '').strip()
        supplier.notes = request.form.get('notes', '').strip()
        
        if not supplier.name:
            flash('الرجاء إدخال اسم المورد', 'error')
            return redirect(url_for('suppliers.edit', id=id))
        
        # Check duplicate
        existing = Supplier.query.filter_by(name=supplier.name).first()
        if existing and existing.id != id:
            flash('اسم المورد موجود بالفعل', 'error')
            return redirect(url_for('suppliers.edit', id=id))
        
        log_action('تعديل مورد', {'id': supplier.id, 'name': supplier.name})
        db.session.commit()
        
        flash('تم تحديث بيانات المورد بنجاح', 'success')
        return redirect(url_for('suppliers.detail', id=id))
    
    return render_template('suppliers/edit.html', supplier=supplier)


# API endpoints
@bp.route('/api/suppliers')
def api_suppliers():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'phone': s.phone,
        'email': s.email
    } for s in suppliers])