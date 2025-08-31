from flask import render_template, request, redirect, url_for, flash, jsonify, make_response, current_app
from acc.blueprints.customers import bp
from acc.extensions import db
from acc.models import Customer, Contract, Voucher, Installment
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from sqlalchemy import or_, func
from acc.services.code_generator import generate_customer_code

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
    
    # ترتيب من الأقدم للأحدث (الكود الأصغر أولاً)
    query = query.order_by(Customer.code.asc())
    pagination = Pagination(query, page)
    
    return render_template('customers/index.html', 
                         customers=pagination.items,
                         pagination=pagination,
                         q=q)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip() or None
            national_id = request.form.get('national_id', '').strip() or None
            address = request.form.get('address', '').strip() or None
            status = request.form.get('status', 'نشط')
            notes = request.form.get('notes', '').strip() or None
            
            # Validation
            if not name:
                flash('❌ الرجاء إدخال اسم العميل', 'error')
                return redirect(url_for('customers.add'))
            
            # Check if customer with same name exists
            existing = Customer.query.filter_by(name=name).first()
            if existing:
                error_msg = f'العميل "{name}" مسجل بالفعل في قاعدة البيانات'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': f'❌ {error_msg}',
                        'duplicate': True,
                        'redirect': url_for('customers.detail', id=existing.id)
                    }), 400
                
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('customers.detail', id=existing.id))
            
            # Validate phone length if provided
            if phone and len(phone) > 20:
                flash('⚠️ رقم الهاتف طويل جداً (الحد الأقصى 20 رقم)', 'warning')
                return redirect(url_for('customers.add'))
            
            # Create new customer with auto-generated code
            customer = Customer(
                id=generate_uid('C'),
                code=generate_customer_code(),
                name=name,
                phone=phone,
                national_id=national_id,
                address=address,
                status=status,
                notes=notes
            )
            
            db.session.add(customer)
            db.session.commit()
            
            # Log action after successful save
            log_action('إضافة عميل جديد', {'id': customer.id, 'name': customer.name})
            
            flash(f'✅ تم إضافة العميل "{name}" بنجاح', 'success')
            
            # Check if it's an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'تم إضافة العميل "{name}" بنجاح',
                    'redirect': url_for('customers.index')
                })
            
            return redirect(url_for('customers.index'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'❌ خطأ في إضافة العميل: {str(e)}'
            flash(error_msg, 'error')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg}), 500
                
            return redirect(url_for('customers.add'))
    
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
        
        if not customer.name:
            flash('الرجاء إدخال اسم العميل.', 'error')
            return redirect(url_for('customers.edit', id=id))
        
        log_action('تعديل بيانات عميل', {'id': customer.id, 'name': customer.name})
        db.session.commit()
        
        flash('تم تحديث بيانات العميل بنجاح.', 'success')
        return redirect(url_for('customers.detail', id=id))
    
    return render_template('customers/edit.html', customer=customer)

@bp.route('/<string:id>/delete', methods=['POST', 'DELETE'])
def delete(id):
    try:
        current_app.logger.info(f"Delete request for customer: {id}")
        
        customer = Customer.query.get_or_404(id)
        
        # Check if customer has contracts
        if len(customer.contracts) > 0:
            error_msg = f'لا يمكن حذف العميل "{customer.name}" لوجود {len(customer.contracts)} عقد مرتبط به.'
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('customers.index'))
        
        # Check if customer has installments
        installments_count = Installment.query.join(Contract).filter(Contract.customer_id == customer.id).count()
        if installments_count > 0:
            error_msg = f'لا يمكن حذف العميل "{customer.name}" لوجود {installments_count} قسط مرتبط به.'
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('customers.index'))
        
        # Check if customer has vouchers
        vouchers_count = Voucher.query.filter_by(customer_id=customer.id).count()
        if vouchers_count > 0:
            error_msg = f'لا يمكن حذف العميل "{customer.name}" لوجود {vouchers_count} سند مرتبط به.'
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('customers.index'))
        
        # Store customer info before deletion
        customer_name = customer.name
        customer_id = customer.id
        
        # Delete the customer
        db.session.delete(customer)
        db.session.commit()
        
        # Log action after successful deletion
        log_action('حذف عميل', {'id': customer_id, 'name': customer_name})
        
        success_msg = f'تم حذف العميل "{customer_name}" بنجاح.'
        
        flash(f'✅ {success_msg}', 'success')
        return redirect(url_for('customers.index'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting customer {id}: {str(e)}", exc_info=True)
        
        # معالجة أنواع الأخطاء المختلفة
        if "foreign key constraint" in str(e).lower():
            error_msg = 'لا يمكن حذف العميل لوجود بيانات مرتبطة به'
        elif "not found" in str(e).lower():
            error_msg = 'العميل غير موجود'
        else:
            error_msg = f'حدث خطأ في حذف العميل: {str(e)}'
            
        flash(f'❌ {error_msg}', 'error')
        return redirect(url_for('customers.index'))

@bp.route('/test-delete')
def test_delete():
    """صفحة اختبار الحذف"""
    customers = Customer.query.all()
    return render_template('customers/test_delete.html', customers=customers)

@bp.route('/search')
def search():
    """Advanced search endpoint for AJAX"""
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    query = Customer.query
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Customer.name.ilike(search_term),
                Customer.phone.ilike(search_term),
                Customer.national_id.ilike(search_term),
                Customer.address.ilike(search_term),
                Customer.code.ilike(search_term)
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Customer.status == status)
    
    # Order by - من الأقدم للأحدث
    query = query.order_by(Customer.code.asc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return only the table part
        return render_template('customers/_results.html',
                             customers=pagination.items,
                             pagination=pagination,
                             q=q,
                             status=status)
    
    # Otherwise return full page
    return render_template('customers/index.html',
                         customers=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status)
