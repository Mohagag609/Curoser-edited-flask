from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.customers import bp
from acc.extensions import db
from acc.models import Customer, Contract, Voucher, Installment
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from sqlalchemy import or_, func
from .simple_export import simple_export_json, simple_export_csv, simple_import_json, simple_import_csv
from .excel_export import export_excel_html, export_report_excel
from .excel_import import import_excel_as_csv


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
        
        if not name:
            flash('الرجاء إدخال اسم العميل.', 'error')
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


@bp.route('/report')
def report():
    """عرض صفحة التقارير"""
    # إحصائيات عامة
    total_customers = Customer.query.count()
    active_customers = Customer.query.filter_by(status='نشط').count()
    inactive_customers = Customer.query.filter_by(status='غير نشط').count()
    
    # العملاء الأكثر شراءً
    top_customers = db.session.query(
        Customer,
        func.count(Contract.id).label('contracts_count'),
        func.sum(Contract.total_price).label('total_value')
    ).join(Contract).group_by(Customer.id).order_by(
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


@bp.route('/export/<format>')
def export(format):
    """تصدير بيانات العملاء"""
    # جلب جميع العملاء
    customers = Customer.query.order_by(Customer.name).all()
    
    if format == 'excel':
        return export_excel_html(customers)
    elif format == 'json':
        return simple_export_json(customers)
    elif format == 'csv':
        return simple_export_csv(customers)
    else:
        flash('صيغة التصدير غير مدعومة', 'error')
        return redirect(url_for('customers.index'))


@bp.route('/import', methods=['GET', 'POST'])
def import_data():
    """استيراد بيانات العملاء"""
    if request.method == 'GET':
        return render_template('customers/import.html')
    
    if 'file' not in request.files:
        flash('الرجاء اختيار ملف', 'error')
        return redirect(url_for('customers.import_data'))
    
    file = request.files['file']
    if file.filename == '':
        flash('الرجاء اختيار ملف', 'error')
        return redirect(url_for('customers.import_data'))
    
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    try:
        imported_count = 0
        skipped_count = 0
        errors = []
        customers_data = []
        
        # استخدام الوظائف المناسبة حسب نوع الملف
        if file_ext in ['xlsx', 'xls']:
            try:
                customers_data = import_excel_as_csv(file)
            except Exception as e:
                flash(f'خطأ في قراءة ملف Excel: {str(e)}', 'error')
                flash('يُرجى التأكد من أن الملف بتنسيق صحيح أو حفظه كـ CSV', 'info')
                return redirect(url_for('customers.import_data'))
        elif file_ext == 'json':
            customers_data = simple_import_json(file)
        elif file_ext == 'csv':
            customers_data = simple_import_csv(file)
        else:
            flash('صيغة الملف غير مدعومة. الرجاء استخدام Excel, JSON أو CSV', 'error')
            return redirect(url_for('customers.import_data'))
        
        # معالجة البيانات المستوردة
        for index, data in enumerate(customers_data):
            try:
                name = data.get('name', '').strip()
                if not name:
                    continue
                
                # التحقق من وجود العميل
                existing = Customer.query.filter_by(name=name).first()
                if existing:
                    skipped_count += 1
                    continue
                
                customer = Customer(
                    id=generate_uid('C'),
                    name=name,
                    phone=data.get('phone'),
                    national_id=data.get('national_id'),
                    address=data.get('address'),
                    status=data.get('status', 'نشط'),
                    notes=data.get('notes')
                )
                
                db.session.add(customer)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"خطأ في السطر {index + 2}: {str(e)}")
        
        # حفظ التغييرات
        if imported_count > 0:
            log_action('استيراد عملاء', {'imported': imported_count, 'skipped': skipped_count})
            db.session.commit()
        
        # عرض النتائج
        if imported_count > 0:
            flash(f'تم استيراد {imported_count} عميل بنجاح', 'success')
        if skipped_count > 0:
            flash(f'تم تخطي {skipped_count} عميل (موجود مسبقاً)', 'info')
        if errors:
            for error in errors[:5]:  # عرض أول 5 أخطاء فقط
                flash(error, 'error')
            if len(errors) > 5:
                flash(f'... و {len(errors) - 5} أخطاء أخرى', 'error')
        
        return redirect(url_for('customers.index'))
        
    except Exception as e:
        flash(f'خطأ في معالجة الملف: {str(e)}', 'error')
        return redirect(url_for('customers.import_data'))


@bp.route('/report/export/<type>')
def export_report(type):
    """تصدير التقارير إلى Excel"""
    if type == 'summary':
        # إحصائيات عامة
        total_customers = Customer.query.count()
        active_customers = Customer.query.filter_by(status='نشط').count()
        inactive_customers = Customer.query.filter_by(status='غير نشط').count()
        
        summary = {
            'إجمالي العملاء': total_customers,
            'العملاء النشطون': active_customers,
            'العملاء غير النشطين': inactive_customers
        }
        
        # إعداد البيانات للجدول
        headers = ['النوع', 'العدد', 'النسبة']
        rows = []
        
        if total_customers > 0:
            rows.append(['العملاء النشطون', active_customers, f'{(active_customers/total_customers*100):.1f}%'])
            rows.append(['العملاء غير النشطين', inactive_customers, f'{(inactive_customers/total_customers*100):.1f}%'])
            rows.append(['الإجمالي', total_customers, '100%'])
        
        return export_report_excel('تقرير إحصائيات العملاء', headers, rows, summary)
    
    elif type == 'top_customers':
        # العملاء الأكثر شراءً
        top_customers = db.session.query(
            Customer,
            func.count(Contract.id).label('contracts_count'),
            func.sum(Contract.total_price).label('total_value')
        ).join(Contract).group_by(Customer.id).order_by(
            func.sum(Contract.total_price).desc()
        ).limit(20).all()
        
        headers = ['اسم العميل', 'عدد العقود', 'إجمالي القيمة', 'الحالة']
        rows = []
        
        total_sum = sum(item[2] or 0 for item in top_customers)
        
        for item in top_customers:
            rows.append([
                item[0].name,
                item[1],
                format_currency(item[2] or 0),
                item[0].status
            ])
        
        summary = {'إجمالي القيمة': format_currency(total_sum)}
        
        return export_report_excel('تقرير العملاء الأكثر شراءً', headers, rows, summary)
    
    elif type == 'debtors':
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
                    'debt': debt,
                    'payment_percentage': (total_paid / total_value * 100) if total_value > 0 else 0
                })
        
        debtors.sort(key=lambda x: x['debt'], reverse=True)
        
        headers = ['اسم العميل', 'إجمالي القيمة', 'المدفوع', 'المتبقي', 'نسبة السداد']
        rows = []
        
        total_debt = sum(d['debt'] for d in debtors)
        total_value_sum = sum(d['total_value'] for d in debtors)
        total_paid_sum = sum(d['total_paid'] for d in debtors)
        
        for debtor in debtors[:50]:  # أول 50 مدين
            rows.append([
                debtor['customer'].name,
                format_currency(debtor['total_value']),
                format_currency(debtor['total_paid']),
                format_currency(debtor['debt']),
                f"{debtor['payment_percentage']:.1f}%"
            ])
        
        summary = {
            'إجمالي المديونية': format_currency(total_debt),
            'إجمالي القيمة': format_currency(total_value_sum),
            'إجمالي المدفوع': format_currency(total_paid_sum)
        }
        
        return export_report_excel('تقرير العملاء المدينون', headers, rows, summary)
    
    else:
        flash('نوع التقرير غير مدعوم', 'error')
        return redirect(url_for('customers.report'))