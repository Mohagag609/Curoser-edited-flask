from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from acc.blueprints.customers import bp
from acc.extensions import db
from acc.models import Customer, Contract, Voucher, Installment
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from sqlalchemy import or_, func
from acc.services.code_generator import generate_customer_code
import csv
import io
from datetime import datetime


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
    
    # استخدام DataTables بدلاً من pagination
    customers = query.all()  # جلب كل العملاء للجدول
    return render_template('customers/index_datatables.html', 
                         customers=customers)


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


@bp.route('/<string:id>/delete', methods=['POST'])
def delete(id):
    try:
        customer = Customer.query.get_or_404(id)
        
        # Check if customer has contracts
        if len(customer.contracts) > 0:
            error_msg = f'لا يمكن حذف العميل "{customer.name}" لوجود عقود مرتبطة به.'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            
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
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True, 
                'message': f'✅ {success_msg}'
            })
        
        flash(f'✅ {success_msg}', 'success')
        return redirect(url_for('customers.index'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'خطأ في حذف العميل: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
        flash(f'❌ {error_msg}', 'error')
        return redirect(url_for('customers.index'))


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
    
    # Order by
    query = query.order_by(Customer.created_at.desc())
    
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


@bp.route('/report')
def report():
    """عرض صفحة التقارير"""
    try:
        # إحصائيات عامة
        total_customers = Customer.query.count()
        active_customers = Customer.query.filter_by(status='نشط').count()
        inactive_customers = Customer.query.filter_by(status='غير نشط').count()
        
        # العملاء الأكثر شراءً
        top_customers = db.session.query(
            Customer,
            func.count(Contract.id).label('contracts_count'),
            func.sum(Contract.total_price).label('total_value')
        ).join(Contract, Customer.id == Contract.customer_id, isouter=True).group_by(Customer.id).order_by(
            func.sum(Contract.total_price).desc()
        ).limit(10).all()
        
        # العملاء المدينون
        debtors = []
        customers_with_contracts = db.session.query(Customer).join(Contract).distinct().all()
        
        for customer in customers_with_contracts:
            total_value = 0
            total_paid = 0
            
            for contract in customer.contracts:
                total_value += contract.total_price or 0
                
                # حساب المدفوعات
                installment_ids = [i.id for i in Installment.query.filter_by(unit_id=contract.unit_id).all()]
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
            
            debt = total_value - total_paid
            if debt > 0:
                debtors.append({
                    'customer': customer,
                    'total_value': total_value,
                    'total_paid': total_paid,
                    'debt': debt
                })
        
        debtors.sort(key=lambda x: x['debt'], reverse=True)
        
        return render_template('customers/report.html',
                             total_customers=total_customers,
                             active_customers=active_customers,
                             inactive_customers=inactive_customers,
                             top_customers=top_customers,
                             debtors=debtors[:10],  # أكبر 10 مدينين
                             format_currency=format_currency)
    except Exception as e:
        flash(f'حدث خطأ في عرض التقارير: {str(e)}', 'error')
        return redirect(url_for('customers.index'))


@bp.route('/export/simple/<format>')
def export_simple(format):
    """تصدير بسيط للعملاء"""
    try:
        customers = Customer.query.order_by(Customer.name).all()
        
        if format == 'csv':
            # تصدير CSV بسيط
            output = io.StringIO()
            writer = csv.writer(output)
            
            # العناوين
            writer.writerow(['الكود', 'الاسم', 'الهاتف', 'الرقم القومي', 'العنوان', 'الحالة'])
            
            # البيانات
            for customer in customers:
                writer.writerow([
                    customer.code,
                    customer.name,
                    customer.phone or '',
                    customer.national_id or '',
                    customer.address or '',
                    customer.status
                ])
            
            # إنشاء الاستجابة
            response = make_response('\ufeff' + output.getvalue())
            response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
            response.headers['Content-Disposition'] = f'attachment; filename=customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            return response
            
        elif format == 'excel':
            # تصدير Excel بسيط باستخدام HTML
            html = render_template('customers/export_excel.html', customers=customers)
            response = make_response(html)
            response.headers['Content-Type'] = 'application/vnd.ms-excel'
            response.headers['Content-Disposition'] = f'attachment; filename=customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
            return response
            
        else:
            flash('صيغة التصدير غير مدعومة', 'error')
            return redirect(url_for('customers.index'))
            
    except Exception as e:
        flash(f'خطأ في التصدير: {str(e)}', 'error')
        return redirect(url_for('customers.index'))


@bp.route('/import/simple', methods=['GET', 'POST'])
def import_simple():
    """صفحة استيراد بسيطة"""
    if request.method == 'GET':
        return render_template('customers/import_simple.html')
    
    if 'file' not in request.files:
        flash('الرجاء اختيار ملف', 'error')
        return redirect(url_for('customers.import_simple'))
    
    file = request.files['file']
    if file.filename == '':
        flash('الرجاء اختيار ملف', 'error')
        return redirect(url_for('customers.import_simple'))
    
    try:
        # قراءة ملف CSV بسيط
        content = file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content))
        
        imported_count = 0
        skipped_count = 0
        
        for row in reader:
            name = row.get('الاسم', '').strip()
            if not name:
                continue
            
            # تحقق من وجود العميل
            if Customer.query.filter_by(name=name).first():
                skipped_count += 1
                continue
            
            # إنشاء عميل جديد
            customer = Customer(
                id=generate_uid('C'),
                code=generate_customer_code(),
                name=name,
                phone=row.get('الهاتف', '').strip() or None,
                national_id=row.get('الرقم القومي', '').strip() or None,
                address=row.get('العنوان', '').strip() or None,
                status=row.get('الحالة', 'نشط').strip()
            )
            
            db.session.add(customer)
            imported_count += 1
        
        if imported_count > 0:
            db.session.commit()
            flash(f'تم استيراد {imported_count} عميل بنجاح', 'success')
        
        if skipped_count > 0:
            flash(f'تم تخطي {skipped_count} عميل مكرر', 'warning')
        
        return redirect(url_for('customers.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'خطأ في الاستيراد: {str(e)}', 'error')
        return redirect(url_for('customers.import_simple'))


@bp.route('/report/simple')
def report_simple():
    """صفحة تقارير حديثة مع رسوم بيانية"""
    try:
        # إحصائيات بسيطة
        total_customers = Customer.query.count()
        active_customers = Customer.query.filter_by(status='نشط').count()
        inactive_customers = total_customers - active_customers
        
        # حساب معدل النمو
        from datetime import datetime, timedelta
        now = datetime.now()
        last_month = now - timedelta(days=30)
        new_customers = Customer.query.filter(Customer.created_at >= last_month).count()
        growth_rate = round((new_customers / max(total_customers - new_customers, 1)) * 100, 1)
        
        # بيانات العملاء الجدد خلال الشهور الماضية
        monthly_labels = []
        monthly_data = []
        for i in range(6):
            month_start = now - timedelta(days=(i+1)*30)
            month_end = now - timedelta(days=i*30)
            count = Customer.query.filter(
                Customer.created_at >= month_start,
                Customer.created_at < month_end
            ).count()
            monthly_labels.insert(0, month_start.strftime('%B'))
            monthly_data.insert(0, count)
        
        return render_template('customers/report_charts.html',
                             total_customers=total_customers,
                             active_customers=active_customers,
                             inactive_customers=inactive_customers,
                             growth_rate=growth_rate,
                             monthly_labels=monthly_labels,
                             monthly_data=monthly_data)
                             
    except Exception as e:
        flash(f'خطأ في عرض التقارير: {str(e)}', 'error')
        return redirect(url_for('customers.index'))



