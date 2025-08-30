from flask import render_template, request, redirect, url_for, flash, jsonify, Response, send_file, g
from acc.blueprints.contracts import bp
from acc.extensions import db
from acc.models import Contract, Customer, Unit, Broker, Installment, Safe, Voucher
from acc.services.utils import generate_uid, log_action, Pagination, format_currency, format_date
from acc.services.import_handler import ImportHandler
from acc.services.code_generator import generate_contract_code
from sqlalchemy import or_, func
import json
import csv
import io
from datetime import datetime, date
from decimal import Decimal


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    
    query = Contract.query.filter_by(project_id=g.project.id)
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.join(Customer).join(Unit).filter(
            or_(
                Contract.code.ilike(search_term),
                Customer.name.ilike(search_term),
                Unit.code.ilike(search_term),
                Unit.name.ilike(search_term)
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Contract.status == status)
    
    # Order by
    query = query.order_by(Contract.date.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Calculate stats
    total_contracts = Contract.query.filter_by(project_id=g.project.id).count()
    active_contracts = Contract.query.filter_by(project_id=g.project.id, status='نشط').count()
    completed_contracts = Contract.query.filter_by(project_id=g.project.id, status='مكتمل').count()
    cancelled_contracts = Contract.query.filter_by(project_id=g.project.id, status='ملغي').count()
    
    return render_template('contracts/index.html',
                         contracts=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status,
                         total_contracts=total_contracts,
                         active_contracts=active_contracts,
                         completed_contracts=completed_contracts,
                         cancelled_contracts=cancelled_contracts,
                         format_currency=format_currency)


@bp.route('/search')
def search():
    """Advanced search endpoint for AJAX"""
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    query = Contract.query.filter_by(project_id=g.project.id)
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.join(Customer).join(Unit).filter(
            or_(
                Contract.code.ilike(search_term),
                Customer.name.ilike(search_term),
                Unit.code.ilike(search_term),
                Unit.name.ilike(search_term)
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Contract.status == status)
    
    # Order by
    query = query.order_by(Contract.date.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('contracts/_results.html',
                             contracts=pagination.items,
                             pagination=pagination,
                             q=q,
                             status=status,
                             format_currency=format_currency)
    
    # Otherwise return full page
    return render_template('contracts/index.html',
                         contracts=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            customer_id = request.form.get('customer_id')
            unit_id = request.form.get('unit_id')
            date_str = request.form.get('date')
            
            if not all([customer_id, unit_id, date_str]):
                error_msg = 'الرجاء ملء جميع الحقول المطلوبة'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('contracts.add'))
            
            # Parse date
            try:
                contract_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                error_msg = 'تاريخ غير صحيح'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('contracts.add'))
            
            # Check if unit is already sold
            existing = Contract.query.filter_by(unit_id=unit_id, project_id=g.project.id).filter(
                Contract.status != 'ملغي'
            ).first()
            
            if existing:
                error_msg = f'هذه الوحدة مباعة بالفعل في العقد رقم {existing.code}'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('contracts.add'))
            
            # Generate code automatically
            code = generate_contract_code()
            
            # Get unit details
            unit = Unit.query.get(unit_id)
            
            contract = Contract(
                id=generate_uid('CNT'),
                code=code,
                project_id=g.project.id,
                customer_id=customer_id,
                unit_id=unit_id,
                date=contract_date,
                unit_price=unit.price,
                booking_amount=Decimal(request.form.get('booking_amount', 0)),
                contract_amount=Decimal(request.form.get('contract_amount', unit.price)),
                broker_id=request.form.get('broker_id') or None,
                broker_commission=Decimal(request.form.get('broker_commission', 0)),
                status='نشط',
                notes=request.form.get('notes', '').strip() or None
            )
            
            # Calculate totals
            contract.paid_amount = contract.booking_amount
            contract.remaining_amount = contract.contract_amount - contract.paid_amount
            
            # Update unit status
            unit.status = 'محجوزة'
            
            db.session.add(contract)
            db.session.commit()
            
            log_action('إضافة عقد', {'id': contract.id, 'code': contract.code})
            
            success_msg = f'تم إضافة العقد بنجاح! رقم العقد: {code}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('contracts.detail', id=contract.id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('contracts.detail', id=contract.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء إضافة العقد: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('contracts.add'))
    
    # Get available units and customers
    customers = Customer.query.filter_by(status='نشط').order_by(Customer.name).all()
    units = Unit.query.filter_by(project_id=g.project.id, status='متاحة').order_by(Unit.code).all()
    brokers = Broker.query.filter_by(status='نشط').order_by(Broker.name).all()
    
    return render_template('contracts/add.html',
                         customers=customers,
                         units=units,
                         brokers=brokers,
                         today=date.today(),
                         format_currency=format_currency)


@bp.route('/<string:id>')
def detail(id):
    contract = Contract.query.get_or_404(id)
    
    # Ensure contract belongs to current project
    if contract.project_id != g.project.id:
        flash('❌ عقد غير موجود', 'error')
        return redirect(url_for('contracts.index'))
    
    # Get installments
    installments = contract.installments.order_by(Installment.due_date).all()
    
    # Calculate statistics
    total_paid = sum(i.paid_amount for i in installments if i.paid_amount)
    total_due = sum(i.amount for i in installments)
    overdue_count = sum(1 for i in installments if i.status == 'متأخر')
    
    return render_template('contracts/detail.html',
                         contract=contract,
                         installments=installments,
                         total_paid=total_paid,
                         total_due=total_due,
                         overdue_count=overdue_count,
                         format_currency=format_currency,
                         format_date=format_date)


@bp.route('/<string:id>/edit', methods=['GET', 'POST'])
def edit(id):
    contract = Contract.query.get_or_404(id)
    
    # Ensure contract belongs to current project
    if contract.project_id != g.project.id:
        flash('❌ عقد غير موجود', 'error')
        return redirect(url_for('contracts.index'))
    
    if request.method == 'POST':
        try:
            # Update contract details
            contract.booking_amount = Decimal(request.form.get('booking_amount', contract.booking_amount))
            contract.contract_amount = Decimal(request.form.get('contract_amount', contract.contract_amount))
            contract.broker_id = request.form.get('broker_id') or None
            contract.broker_commission = Decimal(request.form.get('broker_commission', 0))
            contract.status = request.form.get('status', contract.status)
            contract.notes = request.form.get('notes', '').strip() or None
            
            # Recalculate totals
            paid_installments = sum(i.paid_amount for i in contract.installments if i.paid_amount)
            contract.paid_amount = contract.booking_amount + paid_installments
            contract.remaining_amount = contract.contract_amount - contract.paid_amount
            
            log_action('تعديل عقد', {'id': contract.id, 'code': contract.code})
            db.session.commit()
            
            success_msg = 'تم تعديل العقد بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('contracts.detail', id=id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('contracts.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء تعديل العقد: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('contracts.edit', id=id))
    
    brokers = Broker.query.filter_by(status='نشط').order_by(Broker.name).all()
    
    return render_template('contracts/edit.html',
                         contract=contract,
                         brokers=brokers)


@bp.route('/<string:id>/delete', methods=['POST'])
def delete(id):
    try:
        contract = Contract.query.get_or_404(id)
        
        # Ensure contract belongs to current project
        if contract.project_id != g.project.id:
            error_msg = 'عقد غير موجود'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 404
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('contracts.index'))
        
        # Check if contract has payments
        if contract.installments.filter(Installment.paid_amount > 0).count() > 0:
            error_msg = 'لا يمكن حذف عقد له دفعات مسددة'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('contracts.index'))
        
        contract_code = contract.code
        contract_id = contract.id
        
        # Update unit status
        if contract.unit:
            contract.unit.status = 'متاحة'
        
        # Delete related installments
        Installment.query.filter_by(contract_id=contract.id).delete()
        
        db.session.delete(contract)
        db.session.commit()
        
        log_action('حذف عقد', {'id': contract_id, 'code': contract_code})
        
        success_msg = f'تم حذف العقد "{contract_code}" بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'✅ {success_msg}'
            })
        
        flash(f'✅ {success_msg}', 'success')
        return redirect(url_for('contracts.index'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'خطأ في حذف العقد: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
        
        flash(f'❌ {error_msg}', 'error')
        return redirect(url_for('contracts.index'))


@bp.route('/export')
def export():
    """Export contracts"""
    format = request.args.get('format', 'excel')
    
    contracts = Contract.query.filter_by(project_id=g.project.id).order_by(Contract.date.desc()).all()
    
    if format == 'json':
        # JSON export
        data = []
        for contract in contracts:
            data.append({
                'code': contract.code,
                'date': contract.date.isoformat() if contract.date else '',
                'customer': contract.customer.name if contract.customer else '',
                'unit': contract.unit.code if contract.unit else '',
                'unit_price': float(contract.unit_price),
                'booking_amount': float(contract.booking_amount),
                'contract_amount': float(contract.contract_amount),
                'paid_amount': float(contract.paid_amount),
                'remaining_amount': float(contract.remaining_amount),
                'broker': contract.broker.name if contract.broker else '',
                'broker_commission': float(contract.broker_commission),
                'status': contract.status,
                'notes': contract.notes or ''
            })
        
        output = io.StringIO()
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment;filename=contracts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )
    
    elif format == 'csv':
        # CSV export
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['الكود', 'التاريخ', 'العميل', 'الوحدة', 'سعر الوحدة', 'العربون', 'قيمة العقد', 
                        'المدفوع', 'المتبقي', 'الوسيط', 'عمولة الوسيط', 'الحالة', 'ملاحظات'])
        
        # Data
        for contract in contracts:
            writer.writerow([
                contract.code,
                contract.date.strftime('%Y-%m-%d') if contract.date else '',
                contract.customer.name if contract.customer else '',
                contract.unit.code if contract.unit else '',
                contract.unit_price,
                contract.booking_amount,
                contract.contract_amount,
                contract.paid_amount,
                contract.remaining_amount,
                contract.broker.name if contract.broker else '',
                contract.broker_commission,
                contract.status,
                contract.notes or ''
            ])
        
        output.seek(0)
        output_bytes = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        
        return Response(
            output_bytes.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment;filename=contracts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
    
    else:
        # Excel export (HTML table)
        return render_template('contracts/export_excel.html', 
                             contracts=contracts,
                             datetime=datetime,
                             format_currency=format_currency)


@bp.route('/report')
def report():
    """Generate contracts report"""
    # Get filters
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Contract.query.filter_by(project_id=g.project.id)
    
    # Apply filters
    if status:
        query = query.filter(Contract.status == status)
    
    if date_from:
        query = query.filter(Contract.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    
    if date_to:
        query = query.filter(Contract.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    contracts = query.order_by(Contract.date.desc()).all()
    
    # Calculate statistics
    total_contracts = len(contracts)
    active_contracts = len([c for c in contracts if c.status == 'نشط'])
    completed_contracts = len([c for c in contracts if c.status == 'مكتمل'])
    cancelled_contracts = len([c for c in contracts if c.status == 'ملغي'])
    
    total_value = sum(c.contract_amount for c in contracts)
    total_paid = sum(c.paid_amount for c in contracts)
    total_remaining = sum(c.remaining_amount for c in contracts)
    
    return render_template('contracts/report.html',
                         contracts=contracts,
                         total_contracts=total_contracts,
                         active_contracts=active_contracts,
                         completed_contracts=completed_contracts,
                         cancelled_contracts=cancelled_contracts,
                         total_value=total_value,
                         total_paid=total_paid,
                         total_remaining=total_remaining,
                         status=status,
                         date_from=date_from,
                         date_to=date_to,
                         format_currency=format_currency)