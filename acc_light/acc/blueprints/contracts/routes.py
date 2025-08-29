from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from acc.blueprints.contracts import bp
from acc.extensions import db
from acc.models import Contract, Unit, Customer, Broker, Installment, Voucher
from acc.services.utils import generate_uid, log_action, Pagination, format_currency, get_today
from acc.services.project_context import get_current_project, filter_by_project
from acc.services.code_generator import generate_contract_code
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, func
import io
import csv
import json


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    
    # Start with filtered query by project
    query = filter_by_project(Contract.query, Contract)
    
    if q:
        query = query.join(Contract.customer).join(Contract.unit).filter(
            or_(
                Contract.code.contains(q),
                Customer.name.contains(q),
                Unit.code.contains(q),
                Unit.name.contains(q)
            )
        )
    
    if status_filter:
        query = query.filter(Contract.status == status_filter)
    
    query = query.order_by(Contract.start_date.desc())
    pagination = Pagination(query, page)
    
    # Calculate totals for each contract
    contracts_data = []
    for contract in pagination.items:
        # Calculate paid amount
        installment_ids = [i.id for i in contract.installments]
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
        total_after_discount = contract.total_price - (contract.discount_amount or 0)
        remaining = total_after_discount - paid
        
        contracts_data.append({
            'contract': contract,
            'paid': paid,
            'remaining': remaining,
            'progress': (paid / total_after_discount * 100) if total_after_discount > 0 else 0
        })
    
    return render_template('contracts/index.html',
                         contracts_data=contracts_data,
                         pagination=pagination,
                         q=q,
                         status_filter=status_filter,
                         format_currency=format_currency)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        # Basic data
        customer_id = request.form.get('customer_id')
        unit_id = request.form.get('unit_id')
        payment_method = request.form.get('payment_method', 'installment')
        
        # Contract details
        total_price = float(request.form.get('total_price', 0) or 0)
        discount_amount = float(request.form.get('discount_amount', 0) or 0)
        down_payment = float(request.form.get('down_payment', 0) or 0)
        commission_percentage = float(request.form.get('commission_percentage', 0) or 0)
        maintenance_deposit = float(request.form.get('maintenance_deposit', 0) or 0)
        broker_id = request.form.get('broker_id') or None
        
        # Installment details if applicable
        installment_period = int(request.form.get('installment_period', 0) or 0)
        installment_interval = request.form.get('installment_interval', 'monthly')
        start_date = request.form.get('start_date')
        notes = request.form.get('notes', '').strip()
        
        # Validation
        if not customer_id or not unit_id:
            flash('الرجاء اختيار العميل والوحدة.', 'error')
            return redirect(url_for('contracts.add'))
        
        # Check if unit is available
        unit = Unit.query.get(unit_id)
        if not unit or unit.status == 'مباعة':
            flash('الوحدة غير متاحة للبيع.', 'error')
            return redirect(url_for('contracts.add'))
        
        # Check if unit already has a contract
        existing_contract = Contract.query.filter_by(unit_id=unit_id).first()
        if existing_contract:
            flash('هذه الوحدة لديها عقد بالفعل.', 'error')
            return redirect(url_for('contracts.add'))
        
        # Get current project
        current_project = get_current_project()
        if not current_project:
            flash('الرجاء اختيار مشروع أولاً', 'error')
            return redirect(url_for('projects.index'))
        
        # Create contract
        contract = Contract(
            id=generate_uid('CT'),
            project_id=current_project.id,
            code=generate_contract_code(),  # استخدام الدالة الجديدة
            customer_id=customer_id,
            unit_id=unit_id,
            start_date=datetime.now().date(),
            payment_type=payment_method,
            total_price=total_price or unit.total_price,
            discount_amount=discount_amount,
            down_payment=down_payment,
            broker_name=Broker.query.get(broker_id).name if broker_id else None,
            broker_percent=commission_percentage,
            broker_amount=(total_price or unit.total_price) * commission_percentage / 100 if commission_percentage else 0,
            maintenance_deposit=maintenance_deposit,
            installment_type=installment_interval if payment_method == 'installment' else None,
            installment_count=installment_period if payment_method == 'installment' else 0
        )
        
        try:
            db.session.add(contract)
            
            # Update unit status
            unit.status = 'مباعة'
            
            # Generate installments if payment method is installments
            if payment_method == 'installment' and installment_period > 0:
                generate_installments(contract, installment_interval, start_date)
            
            log_action('إنشاء عقد جديد', {'id': contract.id, 'contract_number': contract.code})
            db.session.commit()
            
            flash(f'✅ تم إنشاء العقد بنجاح! رقم العقد: {contract.code}', 'success')
            
            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'تم إنشاء العقد بنجاح! رقم العقد: {contract.code}',
                    'redirect': url_for('contracts.detail', id=contract.id)
                })
            
            return redirect(url_for('contracts.detail', id=contract.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'❌ حدث خطأ أثناء إنشاء العقد: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg}), 500
            
            flash(error_msg, 'error')
            return redirect(url_for('contracts.add'))
    
    # Get available units and customers
    units = filter_by_project(Unit.query, Unit).filter(Unit.status != 'مباعة').all()
    customers = Customer.query.filter_by(status='نشط').all()
    brokers = Broker.query.filter_by(status='نشط').all()
    
    return render_template('contracts/add.html',
                         units=units,
                         customers=customers,
                         brokers=brokers,
                         today=get_today())


@bp.route('/<string:id>')
def detail(id):
    contract = Contract.query.get_or_404(id)
    
    # Get installments
    installments = Installment.query.filter_by(unit_id=contract.unit_id).order_by(Installment.installment_number).all()
    
    # Calculate payments
    total_after_discount = contract.total_price - (contract.discount_amount or 0)
    
    # Get all payments
    installment_ids = [i.id for i in installments]
    voucher_query = Voucher.query.filter(Voucher.type == 'receipt')
    
    if installment_ids:
        voucher_query = voucher_query.filter(
            or_(
                Voucher.linked_ref == contract.id,
                Voucher.linked_ref.in_(installment_ids)
            )
        )
    else:
        voucher_query = voucher_query.filter(Voucher.linked_ref == contract.id)
    
    payments = voucher_query.all()
    total_paid = sum(p.amount for p in payments)
    remaining = total_after_discount - total_paid
    
    # Calculate installment status
    installments_data = []
    for installment in installments:
        inst_payments = Voucher.query.filter_by(type='receipt', linked_ref=installment.id).all()
        inst_paid = sum(p.amount for p in inst_payments)
        
        status = 'pending'
        if inst_paid >= installment.amount:
            status = 'paid'
        elif inst_paid > 0:
            status = 'partial'
        elif installment.due_date < datetime.now().date():
            status = 'overdue'
        
        installments_data.append({
            'installment': installment,
            'paid': inst_paid,
            'remaining': installment.amount - inst_paid,
            'status': status,
            'payments': inst_payments
        })
    
    return render_template('contracts/detail.html',
                         contract=contract,
                         installments_data=installments_data,
                         payments=payments,
                         total_paid=total_paid,
                         remaining=remaining,
                         total_after_discount=total_after_discount,
                         format_currency=format_currency)


@bp.route('/<string:id>/cancel', methods=['POST'])
def cancel(id):
    contract = Contract.query.get_or_404(id)
    
    if contract.status == 'ملغي':
        flash('هذا العقد ملغي بالفعل.', 'error')
        return redirect(url_for('contracts.detail', id=id))
    
    # Check if there are any payments
    installment_ids = [i.id for i in contract.installments]
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
    
    total_paid = voucher_query.scalar() or 0
    
    if total_paid > 0:
        flash('لا يمكن إلغاء العقد لوجود مدفوعات. يجب إرجاع المدفوعات أولاً.', 'error')
        return redirect(url_for('contracts.detail', id=id))
    
    # Cancel contract
    contract.status = 'ملغي'
    
    # Release unit
    unit = contract.unit
    unit.status = 'متاحة'
    
    # Cancel all installments
    for installment in contract.installments:
        installment.status = 'ملغي'
    
    log_action('إلغاء عقد', {'id': contract.id, 'contract_number': contract.code})
    db.session.commit()
    
    flash('تم إلغاء العقد بنجاح.', 'success')
    return redirect(url_for('contracts.index'))


@bp.route('/search')
def search():
    """HTMX endpoint for live search"""
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Contract.query
    
    if q:
        query = query.join(Contract.customer).join(Contract.unit).filter(
            or_(
                Contract.code.contains(q),
                Customer.name.contains(q),
                Unit.code.contains(q),
                Unit.name.contains(q)
            )
        )
    
    if status_filter:
        query = query.filter(Contract.status == status_filter)
    
    query = query.order_by(Contract.start_date.desc())
    pagination = Pagination(query, page)
    
    # Calculate totals for each contract
    contracts_data = []
    for contract in pagination.items:
        # Calculate paid amount
        installment_ids = [i.id for i in contract.installments]
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
        total_after_discount = contract.total_price - (contract.discount_amount or 0)
        remaining = total_after_discount - paid
        
        contracts_data.append({
            'contract': contract,
            'paid': paid,
            'remaining': remaining,
            'progress': (paid / total_after_discount * 100) if total_after_discount > 0 else 0
        })
    
    return render_template('contracts/_table.html',
                         contracts_data=contracts_data,
                         pagination=pagination,
                         format_currency=format_currency)


# Helper functions
def generate_contract_number():
    """Generate unique contract number"""
    year = datetime.now().year
    # Get last contract number for this year
    last_contract = Contract.query.filter(
        Contract.code.like(f'{year}-%')
    ).order_by(Contract.contract_number.desc()).first()
    
    if last_contract:
        last_number = int(last_contract.code.split('-')[1])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"{year}-{new_number:04d}"


def generate_installments(contract, interval, start_date_str):
    """Generate installments for a contract"""
    # Calculate installment amount
    total_after_discount = contract.total_price - (contract.discount_amount or 0)
    remaining_after_down = total_after_discount - contract.down_payment
    installment_amount = remaining_after_down / contract.installment_count
    
    # Parse start date
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    else:
        start_date = datetime.now().date() + timedelta(days=30)
    
    # Generate installments
    for i in range(contract.installment_count):
        # Calculate due date based on interval
        if interval == 'monthly':
            due_date = start_date + relativedelta(months=i)
        elif interval == 'quarterly':
            due_date = start_date + relativedelta(months=i*3)
        elif interval == 'semi-annual':
            due_date = start_date + relativedelta(months=i*6)
        else:  # annual
            due_date = start_date + relativedelta(years=i)
        
        installment = Installment(
            unit_id=contract.unit_id,
            installment_number=i + 1,
            amount=installment_amount,
            due_date=due_date,
            status='غير مدفوع'
        )
        db.session.add(installment)


@bp.route('/export/<format>')
def export(format):
    """تصدير بيانات العقود"""
    # Get filtered contracts
    query = filter_by_project(Contract.query, Contract)
    contracts = query.order_by(Contract.created_at.desc()).all()
    
    if format == 'excel':
        output = io.StringIO()
        output.write('<html><body><table border="1">')
        output.write('<tr>')
        output.write('<th>رقم العقد</th>')
        output.write('<th>اسم العميل</th>')
        output.write('<th>رقم الوحدة</th>')
        output.write('<th>السعر الإجمالي</th>')
        output.write('<th>المدفوع مقدماً</th>')
        output.write('<th>نوع الدفع</th>')
        output.write('<th>عدد الأقساط</th>')
        output.write('<th>تاريخ العقد</th>')
        output.write('<th>الحالة</th>')
        output.write('</tr>')
        
        for contract in contracts:
            output.write('<tr>')
            output.write(f'<td>{contract.code}</td>')
            output.write(f'<td>{contract.customer.name if contract.customer else ""}</td>')
            output.write(f'<td>{contract.unit.code if contract.unit else ""}</td>')
            output.write(f'<td>{format_currency(contract.total_price)}</td>')
            output.write(f'<td>{format_currency(contract.down_payment)}</td>')
            output.write(f'<td>{"نقدي" if contract.payment_type == "cash" else "تقسيط"}</td>')
            output.write(f'<td>{contract.installment_count or 0}</td>')
            output.write(f'<td>{contract.start_date}</td>')
            output.write(f'<td>{contract.status}</td>')
            output.write('</tr>')
        
        output.write('</table></body></html>')
        
        response = Response(output.getvalue(), content_type='application/vnd.ms-excel')
        response.headers['Content-Disposition'] = f'attachment; filename=contracts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
        return response
    
    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['رقم العقد', 'اسم العميل', 'رقم الوحدة', 'السعر الإجمالي', 'المدفوع مقدماً', 'نوع الدفع', 'عدد الأقساط', 'تاريخ العقد', 'الحالة'])
        
        for contract in contracts:
            writer.writerow([
                contract.code,
                contract.customer.name if contract.customer else '',
                contract.unit.code if contract.unit else '',
                contract.total_price,
                contract.down_payment,
                'نقدي' if contract.payment_type == 'cash' else 'تقسيط',
                contract.installment_count or 0,
                contract.start_date,
                contract.status
            ])
        
        output.seek(0)
        response = Response(output.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response.headers['Content-Disposition'] = f'attachment; filename=contracts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return response
    
    elif format == 'json':
        data = []
        for contract in contracts:
            data.append({
                'code': contract.code,
                'customer_name': contract.customer.name if contract.customer else '',
                'unit_code': contract.unit.code if contract.unit else '',
                'total_price': float(contract.total_price),
                'down_payment': float(contract.down_payment),
                'payment_type': contract.payment_type,
                'installment_count': contract.installment_count or 0,
                'start_date': contract.start_date.isoformat() if contract.start_date else None,
                'status': contract.status
            })
        
        return jsonify(data)
    
    return redirect(url_for('contracts.index'))


@bp.route('/report')
def report():
    """صفحة التقارير"""
    # Get current project
    current_project = get_current_project()
    
    # إحصائيات عامة
    query = filter_by_project(Contract.query, Contract)
    total_contracts = query.count()
    active_contracts = query.filter_by(status='نشط').count()
    
    # إحصائيات مالية
    total_value = db.session.query(func.sum(Contract.total_price)).filter(
        Contract.project_id == current_project.id if current_project else True
    ).scalar() or 0
    
    total_paid = 0
    contracts = query.all()
    
    for contract in contracts:
        installment_ids = [i.id for i in contract.installments]
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
    
    total_remaining = total_value - total_paid
    
    # العقود الأخيرة
    recent_contracts = query.order_by(Contract.created_at.desc()).limit(10).all()
    
    # العقود المتأخرة في السداد
    overdue_contracts = []
    for contract in contracts:
        if contract.payment_type == 'installment':
            overdue_installments = Installment.query.filter(
                Installment.unit_id == contract.unit_id,
                Installment.due_date < datetime.now().date(),
                Installment.status != 'مدفوع'
            ).count()
            
            if overdue_installments > 0:
                overdue_contracts.append({
                    'contract': contract,
                    'overdue_count': overdue_installments
                })
    
    return render_template('contracts/report.html',
                         total_contracts=total_contracts,
                         active_contracts=active_contracts,
                         total_value=total_value,
                         total_paid=total_paid,
                         total_remaining=total_remaining,
                         recent_contracts=recent_contracts,
                         overdue_contracts=overdue_contracts,
                         format_currency=format_currency)


@bp.route('/report/export/<type>')
def export_report(type):
    """تصدير تقارير مخصصة إلى Excel"""
    current_project = get_current_project()
    output = io.StringIO()
    
    if type == 'general':
        # إحصائيات عامة
        query = filter_by_project(Contract.query, Contract)
        total_contracts = query.count()
        active_contracts = query.filter_by(status='نشط').count()
        
        total_value = db.session.query(func.sum(Contract.total_price)).filter(
            Contract.project_id == current_project.id if current_project else True
        ).scalar() or 0
        
        output.write('<html><head><meta charset="utf-8"></head><body>')
        output.write('<h1>تقرير إحصائيات العقود</h1>')
        output.write('<table border="1">')
        output.write('<tr><th>البيان</th><th>القيمة</th></tr>')
        output.write(f'<tr><td>إجمالي العقود</td><td>{total_contracts}</td></tr>')
        output.write(f'<tr><td>عقود نشطة</td><td>{active_contracts}</td></tr>')
        output.write(f'<tr><td>القيمة الإجمالية</td><td>{format_currency(total_value)}</td></tr>')
        output.write('</table></body></html>')
        
    elif type == 'recent':
        # العقود الأخيرة
        query = filter_by_project(Contract.query, Contract)
        recent_contracts = query.order_by(Contract.created_at.desc()).limit(10).all()
        
        output.write('<html><head><meta charset="utf-8"></head><body>')
        output.write('<h1>أحدث العقود</h1>')
        output.write('<table border="1">')
        output.write('<tr><th>رقم العقد</th><th>العميل</th><th>الوحدة</th><th>القيمة</th><th>التاريخ</th><th>الحالة</th></tr>')
        
        for contract in recent_contracts:
            output.write('<tr>')
            output.write(f'<td>{contract.code}</td>')
            output.write(f'<td>{contract.customer.name if contract.customer else ""}</td>')
            output.write(f'<td>{contract.unit.code if contract.unit else ""}</td>')
            output.write(f'<td>{format_currency(contract.total_price)}</td>')
            output.write(f'<td>{contract.start_date.strftime("%Y-%m-%d") if contract.start_date else ""}</td>')
            output.write(f'<td>{contract.status}</td>')
            output.write('</tr>')
        
        output.write('</table></body></html>')
        
    elif type == 'overdue':
        # العقود المتأخرة
        query = filter_by_project(Contract.query, Contract)
        contracts = query.all()
        
        output.write('<html><head><meta charset="utf-8"></head><body>')
        output.write('<h1>العقود المتأخرة في السداد</h1>')
        output.write('<table border="1">')
        output.write('<tr><th>رقم العقد</th><th>العميل</th><th>الوحدة</th><th>عدد الأقساط المتأخرة</th></tr>')
        
        for contract in contracts:
            if contract.payment_type == 'installment':
                overdue_installments = Installment.query.filter(
                    Installment.unit_id == contract.unit_id,
                    Installment.due_date < datetime.now().date(),
                    Installment.status != 'مدفوع'
                ).count()
                
                if overdue_installments > 0:
                    output.write('<tr>')
                    output.write(f'<td>{contract.code}</td>')
                    output.write(f'<td>{contract.customer.name if contract.customer else ""}</td>')
                    output.write(f'<td>{contract.unit.code if contract.unit else ""}</td>')
                    output.write(f'<td>{overdue_installments}</td>')
                    output.write('</tr>')
        
        output.write('</table></body></html>')
    
    response = Response(output.getvalue(), content_type='application/vnd.ms-excel')
    response.headers['Content-Disposition'] = f'attachment; filename=contract_report_{type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
    return response
