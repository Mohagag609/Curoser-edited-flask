from flask import render_template, request, redirect, url_for, flash, jsonify, g
from acc.blueprints.contracts import bp
from acc.extensions import db
from acc.models import Contract, Customer, Unit, Broker, Installment, Safe, Voucher
from acc.services.utils import generate_uid, log_action, Pagination, format_currency, format_date
from acc.services.code_generator import generate_contract_code
from acc.services.contract_service import generate_installments_for_contract
from acc.services.financial_service import get_contract_financials
from sqlalchemy import or_, func
from decimal import Decimal
from datetime import datetime

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
            # --- Form Data Extraction ---
            customer_id = request.form.get('customer_id')
            unit_id = request.form.get('unit_id')
            start_date_str = request.form.get('start_date') or datetime.today().strftime('%Y-%m-%d')
            
            # --- Basic Validation ---
            if not all([customer_id, unit_id, start_date_str]):
                raise ValueError("الرجاء ملء جميع الحقول الأساسية: العميل، الوحدة، وتاريخ البدء.")

            unit = Unit.query.get_or_404(unit_id)
            if unit.status not in ['متاحة', 'محجوزة']:
                raise ValueError(f"هذه الوحدة غير متاحة للبيع. حالتها: {unit.status}")

            # --- Create Contract Instance ---
            contract = Contract(
                id=generate_uid('CNT'),
                code=generate_contract_code(),
                project_id=g.project.id,
                customer_id=customer_id,
                unit_id=unit_id,
                start_date=datetime.strptime(start_date_str, '%Y-%m-%d').date(),
                total_price=Decimal(request.form.get('total_price') or unit.price),
                down_payment=Decimal(request.form.get('down_payment', 0)),
                discount_amount=Decimal(request.form.get('discount_amount', 0)),
                maintenance_deposit=Decimal(request.form.get('maintenance_deposit', 0)),
                broker_name=request.form.get('broker_name'),
                broker_percent=Decimal(request.form.get('broker_percent', 0)),
                commission_safe_id=request.form.get('commission_safe_id'),
                payment_type=request.form.get('payment_type', 'installment'),
                installment_type=request.form.get('installment_type'),
                installment_count=int(request.form.get('installment_count', 0)),
                extra_annual=int(request.form.get('extra_annual', 0)),
                annual_payment_value=Decimal(request.form.get('annual_payment_value', 0)),
                status='نشط'
            )
            
            # --- Advanced Validation ---
            down_payment_safe_id = request.form.get('down_payment_safe_id')
            if contract.down_payment > 0 and not down_payment_safe_id:
                raise ValueError("الرجاء تحديد خزنة استلام المقدم.")

            # Calculate broker amount
            contract.broker_amount = round((contract.total_price * contract.broker_percent) / 100, 2)
            if contract.broker_amount > 0 and not contract.commission_safe_id:
                raise ValueError("الرجاء تحديد خزنة صرف عمولة السمسار.")

            # --- Database Operations ---
            db.session.add(contract)
            
            # Update unit status
            unit.status = 'مباعة'
            
            # Handle down payment voucher
            if contract.down_payment > 0:
                down_payment_safe = Safe.query.get(down_payment_safe_id)
                if not down_payment_safe:
                    raise ValueError("خزنة المقدم المحددة غير موجودة.")

                down_payment_safe.balance += contract.down_payment

                voucher = Voucher(
                    id=generate_uid('V'),
                    project_id=g.project.id,
                    type='receipt',
                    date=contract.start_date,
                    amount=contract.down_payment,
                    safe_id=down_payment_safe_id,
                    description=f"مقدم عقد للوحدة {unit.code}",
                    payer=contract.customer.name,
                    linked_ref=contract.id,
                    entity_type='customer',
                    entity_id=contract.customer_id
                )
                db.session.add(voucher)
            
            # Commit contract first to get an ID
            db.session.commit()
            
            # Generate installments using the new service
            generate_installments_for_contract(contract)
            
            log_action('إضافة عقد وتوليد أقساط', {'id': contract.id, 'code': contract.code})
            flash(f'✅ تم إضافة العقد "{contract.code}" وتوليد الأقساط بنجاح.', 'success')
            return redirect(url_for('contracts.detail', id=contract.id))

        except ValueError as e:
            db.session.rollback()
            flash(f'❌ خطأ في البيانات: {str(e)}', 'error')
            return redirect(url_for('contracts.add'))
        except Exception as e:
            db.session.rollback()
            flash(f'❌ حدث خطأ غير متوقع أثناء إضافة العقد: {str(e)}', 'error')
            return redirect(url_for('contracts.add'))

    # --- GET Request Handling ---
    customers = Customer.query.filter_by(status='نشط').order_by(Customer.name).all()
    units = Unit.query.filter_by(project_id=g.project.id, status='متاحة').order_by(Unit.code).all()
    safes = Safe.query.all()
    
    return render_template('contracts/add.html',
                         customers=customers,
                         units=units,
                         safes=safes,
                         today=datetime.today().strftime('%Y-%m-%d'),
                         format_currency=format_currency)

@bp.route('/<string:id>')
def detail(id):
    contract = Contract.query.get_or_404(id)
    
    if contract.project_id != g.project.id:
        flash('❌ عقد غير موجود', 'error')
        return redirect(url_for('contracts.index'))
    
    # Get installments, ordered by due date
    installments = sorted(contract.installments, key=lambda x: x.due_date)
    
    # Use the centralized financial service
    financials = get_contract_financials(contract)

    overdue_installments = [
        i for i in installments
        if i.status != 'مدفوع' and i.due_date and i.due_date < datetime.today().date()
    ]
    
    return render_template('contracts/detail.html',
                         contract=contract,
                         installments=installments,
                         financials=financials,
                         overdue_count=len(overdue_installments),
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
        
        if contract.project_id != g.project.id:
            raise ValueError("عقد غير موجود أو لا ينتمي لهذا المشروع.")

        # Find all related vouchers (down payment and installment payments)
        installment_ids = [inst.id for inst in contract.installments]
        vouchers_to_delete = Voucher.query.filter(
            or_(
                Voucher.linked_ref == contract.id,
                Voucher.linked_ref.in_(installment_ids)
            )
        ).all()

        # Reverse financial transactions
        for voucher in vouchers_to_delete:
            if voucher.type == 'receipt':
                safe = voucher.safe
                if safe:
                    safe.balance -= voucher.amount
            # In the future, handle payment vouchers if commissions are paid
            db.session.delete(voucher)
        
        # Update unit status to 'Available'
        if contract.unit:
            contract.unit.status = 'متاحة'

        contract_code = contract.code
        contract_id = contract.id
        
        # SQLAlchemy's cascade delete will handle associated installments
        db.session.delete(contract)
        
        db.session.commit()
        
        log_action('حذف عقد وكل ما يتعلق به', {'id': contract_id, 'code': contract_code})
        
        flash(f'✅ تم حذف العقد "{contract_code}" وجميع أقساطه ومدفوعاته بنجاح.', 'success')
        return redirect(url_for('contracts.index'))

    except Exception as e:
        db.session.rollback()
        flash(f'❌ خطأ في حذف العقد: {str(e)}', 'error')
        return redirect(url_for('contracts.index'))

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