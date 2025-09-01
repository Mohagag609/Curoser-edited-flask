from flask import render_template, request, redirect, url_for, flash, jsonify, g, current_app as app, make_response
from acc.blueprints.contracts import bp
from functools import wraps
from acc.extensions import db
from acc.models import Contract, Customer, Unit, Broker, Installment, Safe, Voucher
from acc.services.utils import generate_uid, log_action, Pagination, format_currency, format_date
from acc.services.code_generator import generate_contract_code
from sqlalchemy import or_, func
from decimal import Decimal
from datetime import date, datetime, timedelta

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    
    # Always join with customer and unit for display
    query = Contract.query.filter_by(project_id=g.project.id)\
                          .outerjoin(Customer)\
                          .outerjoin(Unit)
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
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
    query = query.order_by(Contract.start_date.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Calculate stats
    total_contracts = Contract.query.filter_by(project_id=g.project.id).count()
    active_contracts = Contract.query.filter_by(project_id=g.project.id, status='نشط').count()
    completed_contracts = Contract.query.filter_by(project_id=g.project.id, status='مكتمل').count()
    cancelled_contracts = Contract.query.filter_by(project_id=g.project.id, status='ملغي').count()
    
    # Get safes for contract form
    try:
        safes = Safe.query.filter_by(status='نشط').all()
    except:
        safes = []
    
    return render_template('contracts/index_pro.html',
                         contracts=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status,
                         total_contracts=total_contracts,
                         active_contracts=active_contracts,
                         completed_contracts=completed_contracts,
                         cancelled_contracts=cancelled_contracts,
                         customers=Customer.query.filter_by(status='نشط').order_by(Customer.name).all(),
                         units=Unit.query.filter_by(project_id=g.project.id, status='متاحة').order_by(Unit.code).all(),
                         safes=safes,
                         today=date.today(),
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
        query = query.outerjoin(Customer).outerjoin(Unit).filter(
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
    query = query.order_by(Contract.start_date.desc())
    
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
            contract.total_price = Decimal(request.form.get('total_price', contract.total_price))
            contract.down_payment = Decimal(request.form.get('down_payment', contract.down_payment))
            contract.broker_name = request.form.get('broker_name') or None
            contract.broker_percent = Decimal(request.form.get('broker_percent', 0))
            contract.broker_amount = (contract.total_price * contract.broker_percent) / 100 if contract.broker_percent > 0 else 0
            contract.status = request.form.get('status', contract.status)
            contract.maintenance_deposit = Decimal(request.form.get('maintenance_deposit', contract.maintenance_deposit))
            
            # No need to recalculate - these fields don't exist in our model
            
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
        query = query.filter(Contract.start_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    
    if date_to:
        query = query.filter(Contract.start_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    contracts = query.order_by(Contract.start_date.desc()).all()
    
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


@bp.route('/create', methods=['POST'])
def create():
    """Add contract via AJAX"""
    try:
        # Get form data
        customer_id = request.form.get('customer_id')
        unit_id = request.form.get('unit_id')
        total_price = float(request.form.get('total_price', 0))
        down_payment = float(request.form.get('down_payment', 0))
        
        # Validate required fields
        if not all([customer_id, unit_id]):
            return jsonify({'success': False, 'message': 'الرجاء ملء جميع الحقول المطلوبة'})
        
        # Check if unit is available
        unit = Unit.query.get(unit_id)
        if not unit or unit.status != 'متاحة':
            return jsonify({'success': False, 'message': 'الوحدة غير متاحة'})
        
        # Create contract
        safe_id = request.form.get('safe_id')
        if safe_id == '':
            safe_id = None
            
        contract = Contract(
            id=generate_uid('CNT'),
            code=generate_contract_code(),
            project_id=g.project.id,
            customer_id=customer_id,
            unit_id=unit_id,
            total_price=total_price,
            down_payment=down_payment,
            broker_name=request.form.get('broker_name') or None,
            broker_percent=float(request.form.get('broker_percent', 0)),
            payment_type=request.form.get('payment_type', 'cash'),
            start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
            commission_safe_id=safe_id,
            maintenance_deposit=float(request.form.get('maintenance_deposit', 0)),
            status='نشط'
        )
        
        # Calculate broker amount
        if contract.broker_percent > 0:
            contract.broker_amount = (contract.total_price * contract.broker_percent) / 100
        
        # Update unit status
        unit.status = 'مباعة'
        
        db.session.add(contract)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حفظ العقد بنجاح',
            'contract_id': contract.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})


@bp.route('/<string:id>/generate_installments', methods=['POST'])
def generate_installments(id):
    """Generate installments for a contract"""
    try:
        contract = Contract.query.get_or_404(id)
        
        if contract.payment_type != 'installment':
            return jsonify({'success': False, 'message': 'العقد ليس بنظام التقسيط'})
        
        # Get installment details from form
        installment_type_str = request.form.get('installment_type', 'شهري')
        years = int(request.form.get('years', 1))
        
        # Map installment type string to number
        installment_type_map = {
            'شهري': 12,
            'ربع سنوي': 4,
            'نصف سنوي': 2,
            'سنوي': 1
        }
        installment_type = installment_type_map.get(installment_type_str, 12)
        
        # Calculate installment details
        remaining = contract.total_price - contract.down_payment
        total_installments = installment_type * years
        installment_amount = remaining / total_installments
        
        # Generate installments
        start_date = contract.start_date
        for i in range(total_installments):
            # Calculate due date based on installment type
            if installment_type == 12:  # Monthly
                # Add months properly
                year = start_date.year + ((start_date.month + i) // 12)
                month = ((start_date.month + i - 1) % 12) + 1
                try:
                    due_date = start_date.replace(year=year, month=month)
                except ValueError:
                    # Handle end of month cases (e.g., Jan 31 -> Feb 28)
                    due_date = start_date.replace(year=year, month=month, day=1) + timedelta(days=32)
                    due_date = due_date.replace(day=1) - timedelta(days=1)
            elif installment_type == 4:  # Quarterly
                months_to_add = i * 3
                year = start_date.year + ((start_date.month + months_to_add - 1) // 12)
                month = ((start_date.month + months_to_add - 1) % 12) + 1
                try:
                    due_date = start_date.replace(year=year, month=month)
                except ValueError:
                    due_date = start_date.replace(year=year, month=month, day=1) + timedelta(days=32)
                    due_date = due_date.replace(day=1) - timedelta(days=1)
            elif installment_type == 2:  # Semi-annual
                months_to_add = i * 6
                year = start_date.year + ((start_date.month + months_to_add - 1) // 12)
                month = ((start_date.month + months_to_add - 1) % 12) + 1
                try:
                    due_date = start_date.replace(year=year, month=month)
                except ValueError:
                    due_date = start_date.replace(year=year, month=month, day=1) + timedelta(days=32)
                    due_date = due_date.replace(day=1) - timedelta(days=1)
            else:  # Annual
                due_date = start_date.replace(year=start_date.year + i)
            
            installment = Installment(
                id=generate_uid('INS'),
                unit_id=contract.unit_id,
                installment_number=i + 1,
                due_date=due_date,
                amount=installment_amount,
                status='غير مدفوع',
                type=installment_type_str
            )
            db.session.add(installment)
        
        # Add extra annual payments if specified
        extra_annual = int(request.form.get('extra_annual', 0))
        annual_payment_value = float(request.form.get('annual_payment_value', 0))
        if extra_annual > 0 and annual_payment_value > 0:
            for i in range(extra_annual):
                due_date = start_date.replace(year=start_date.year + i + 1)
                installment = Installment(
                    id=generate_uid('INS'),
                    unit_id=contract.unit_id,
                    installment_number=total_installments + i + 1,
                    due_date=due_date,
                    amount=annual_payment_value,
                    status='غير مدفوع',
                    type='دفعة سنوية إضافية'
                )
                db.session.add(installment)
        
        # Add maintenance deposit as last installment if exists
        maintenance_deposit = float(request.form.get('maintenance_deposit', contract.maintenance_deposit or 0))
        if maintenance_deposit > 0:
            last_date = start_date.replace(year=start_date.year + years)
            installment = Installment(
                id=generate_uid('INS'),
                unit_id=contract.unit_id,
                installment_number=total_installments + extra_annual + 1,
                due_date=last_date,
                amount=maintenance_deposit,
                status='غير مدفوع',
                type='وديعة صيانة'
            )
            db.session.add(installment)
        
        # Update contract
        contract.installment_type = installment_type_str
        contract.installment_count = total_installments
        contract.extra_annual = extra_annual
        contract.annual_payment_value = annual_payment_value
        
        db.session.commit()
        
        total_generated = total_installments + extra_annual + (1 if maintenance_deposit > 0 else 0)
        
        return jsonify({
            'success': True,
            'message': f'تم توليد {total_generated} قسط بنجاح',
            'details': {
                'regular': total_installments,
                'extra_annual': extra_annual,
                'maintenance': 1 if maintenance_deposit > 0 else 0
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'حدث خطأ: {str(e)}'})


# Single delete endpoint with improved error handling
@bp.route('/<string:id>/delete', methods=['POST', 'OPTIONS'])
@bp.route('/delete/<string:id>', methods=['POST', 'OPTIONS'])  # Alternative route
@bp.route('/api/delete/<string:id>', methods=['POST', 'OPTIONS'])  # API route for clarity
def delete(id):
    """Delete contract via AJAX"""
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'
        return response, 200
        
    try:
        # Log for debugging
        app.logger.info(f"Delete request for contract {id}")
        app.logger.info(f"Request method: {request.method}")
        app.logger.info(f"Request path: {request.path}")
        app.logger.info(f"Request headers: {dict(request.headers)}")
        
        # Check if user is logged in and has project
        if not hasattr(g, 'project') or not g.project:
            app.logger.warning(f"No project in g for delete request")
            return jsonify({'success': False, 'message': 'الرجاء اختيار مشروع أولاً'}), 401
        
        # Get the contract
        contract = Contract.query.filter_by(id=id, project_id=g.project.id).first()
        if not contract:
            app.logger.warning(f"Contract {id} not found for project {g.project.id}")
            return jsonify({'success': False, 'message': 'العقد غير موجود'}), 404
        
        # Check if contract has installments
        from acc.models import Installment as InstallmentModel
        has_installments = InstallmentModel.query.filter_by(unit_id=contract.unit_id).count() > 0 if contract.unit_id else False
        
        if has_installments:
            return jsonify({'success': False, 'message': 'لا يمكن حذف عقد له أقساط'}), 400
        
        # Update unit status
        if contract.unit:
            contract.unit.status = 'متاحة'
        
        # Delete the contract
        contract_code = contract.code
        db.session.delete(contract)
        db.session.commit()
        
        log_action('حذف عقد', {'id': id, 'code': contract_code})
        
        return jsonify({'success': True, 'message': 'تم حذف العقد بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting contract: {str(e)}")
        app.logger.error(f"Error type: {type(e).__name__}")
        import traceback
        app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'حدث خطأ في حذف العقد: {str(e)}'}), 500




# Simple test endpoint
@bp.route('/test-delete', methods=['GET', 'POST'])
def test_delete():
    """Test endpoint to verify routing"""
    return jsonify({'success': True, 'message': 'Delete endpoint is working', 'method': request.method})


@bp.route('/<string:id>')
def view(id):
    contract = Contract.query.get_or_404(id)
    
    # Ensure contract belongs to current project
    if contract.project_id != g.project.id:
        flash('❌ عقد غير موجود', 'error')
        return redirect(url_for('contracts.index'))
    
    # Get installments - using direct query to avoid property issues
    from acc.models import Installment as InstallmentModel
    installments = InstallmentModel.query.filter_by(unit_id=contract.unit_id).order_by(InstallmentModel.due_date).all() if contract.unit_id else []
    
    # Calculate statistics
    total_paid = sum(i.get_paid_amount() for i in installments if hasattr(i, 'get_paid_amount'))
    total_due = sum(i.amount for i in installments if i.amount)
    overdue_count = sum(1 for i in installments if i.status == 'متأخر')
    
    return render_template('contracts/view.html',
                         contract=contract,
                         installments=installments,
                         total_paid=total_paid,
                         total_due=total_due,
                         overdue_count=overdue_count,
                         format_currency=format_currency,
                         format_date=format_date)




