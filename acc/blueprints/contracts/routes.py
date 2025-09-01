from flask import render_template, request, redirect, url_for, flash, jsonify, g
from acc.blueprints.contracts import bp
from acc.extensions import db
from acc.models import Contract, Customer, Unit, Safe, Installment
from acc.services.utils import generate_uid, log_action, Pagination, format_currency, format_date
from acc.services.code_generator import generate_contract_code
from sqlalchemy import or_, and_
from decimal import Decimal
from datetime import datetime, timedelta
import json

@bp.route('/')
def index():
    """عرض قائمة العقود"""
    # Clean up any failed transactions
    try:
        db.session.rollback()
    except:
        pass
    
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    
    # البحث والتصفية
    query = Contract.query.filter_by(project_id=g.project.id)
    
    if q:
        search_term = f'%{q}%'
        # Use outer joins to handle missing relationships
        query = query.outerjoin(Customer).outerjoin(Unit).filter(
            or_(
                Contract.code.ilike(search_term),
                Customer.name.ilike(search_term),
                Unit.name.ilike(search_term),
                Unit.code.ilike(search_term)
            )
        )
    
    if status:
        query = query.filter(Contract.status == status)
    
    # الترتيب والترقيم
    query = query.order_by(Contract.created_at.desc())
    pagination = Pagination(query, page, per_page=20)
    
    # الإحصائيات
    stats = {
        'total': Contract.query.filter_by(project_id=g.project.id).count(),
        'active': Contract.query.filter_by(project_id=g.project.id, status='نشط').count(),
        'completed': Contract.query.filter_by(project_id=g.project.id, status='مكتمل').count(),
        'cancelled': Contract.query.filter_by(project_id=g.project.id, status='ملغي').count()
    }
    
    return render_template('contracts/index.html',
                         contracts=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status,
                         stats=stats)

@bp.route('/create', methods=['GET', 'POST'])
def create():
    """إنشاء عقد جديد"""
    if request.method == 'POST':
        try:
            # البيانات الأساسية
            unit_id = request.form.get('unit_id')
            customer_id = request.form.get('customer_id')
            
            # التحقق من الوحدة والعميل
            unit = Unit.query.get_or_404(unit_id)
            customer = Customer.query.get_or_404(customer_id)
            
            if unit.status != 'متاحة':
                raise Exception('الوحدة غير متاحة للبيع')
            
            # إنشاء العقد
            contract = Contract(
                id=generate_uid('CNT'),
                project_id=g.project.id,
                code=generate_contract_code(g.project.id),
                unit_id=unit_id,
                customer_id=customer_id,
                total_price=Decimal(request.form.get('total_price', unit.total_price)),
                down_payment=Decimal(request.form.get('down_payment', 0)),
                maintenance_deposit=Decimal(request.form.get('maintenance_deposit', 0)),
                broker_name=request.form.get('broker_name'),
                broker_percent=Decimal(request.form.get('broker_percent', 0)),
                payment_type=request.form.get('payment_type', 'cash'),
                start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
                status='نشط'
            )
            
            # حساب عمولة السمسار
            if contract.broker_percent > 0:
                contract.broker_amount = (contract.total_price * contract.broker_percent) / 100
            
            # تحديث حالة الوحدة
            unit.status = 'محجوزة'
            
            db.session.add(contract)
            db.session.commit()
            
            # توليد الأقساط إذا كان السداد بالتقسيط
            if contract.payment_type == 'installment':
                generate_installments(contract.id)
            
            log_action('إضافة عقد', {'id': contract.id, 'code': contract.code})
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'تم إنشاء العقد بنجاح',
                    'contract_id': contract.id
                })
            
            flash('تم إنشاء العقد بنجاح', 'success')
            return redirect(url_for('contracts.view', id=contract.id))
            
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)}), 400
            flash(f'خطأ: {str(e)}', 'error')
            return redirect(url_for('contracts.create'))
    
    # عرض النموذج
    customers = Customer.query.filter_by(status='نشط').order_by(Customer.name).all()
    units = Unit.query.filter_by(project_id=g.project.id, status='متاحة').order_by(Unit.code).all()
    safes = Safe.query.filter_by(project_id=g.project.id, status='نشط').all()
    
    return render_template('contracts/create.html',
                         customers=customers,
                         units=units,
                         safes=safes,
                         today=datetime.today().date())

@bp.route('/<string:id>')
def view(id):
    """عرض تفاصيل العقد"""
    contract = Contract.query.get_or_404(id)
    
    if contract.project_id != g.project.id:
        flash('العقد غير موجود', 'error')
        return redirect(url_for('contracts.index'))
    
    # جلب الأقساط
    installments = Installment.query.filter_by(
        contract_id=contract.id
    ).order_by(Installment.due_date).all()
    
    # حساب الإحصائيات
    total_installments = len(installments)
    paid_installments = sum(1 for i in installments if i.status == 'مدفوع')
    total_paid = sum(i.get_paid_amount() for i in installments)
    remaining_amount = contract.total_price - contract.down_payment - total_paid
    
    return render_template('contracts/view.html',
                         contract=contract,
                         installments=installments,
                         stats={
                             'total_installments': total_installments,
                             'paid_installments': paid_installments,
                             'total_paid': total_paid,
                             'remaining_amount': remaining_amount
                         })

@bp.route('/<string:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """تعديل العقد"""
    contract = Contract.query.get_or_404(id)
    
    if contract.project_id != g.project.id:
        flash('العقد غير موجود', 'error')
        return redirect(url_for('contracts.index'))
    
    if request.method == 'POST':
        try:
            # تحديث البيانات
            contract.total_price = Decimal(request.form.get('total_price'))
            contract.down_payment = Decimal(request.form.get('down_payment'))
            contract.maintenance_deposit = Decimal(request.form.get('maintenance_deposit', 0))
            contract.broker_name = request.form.get('broker_name')
            contract.broker_percent = Decimal(request.form.get('broker_percent', 0))
            contract.status = request.form.get('status')
            
            # إعادة حساب عمولة السمسار
            if contract.broker_percent > 0:
                contract.broker_amount = (contract.total_price * contract.broker_percent) / 100
            else:
                contract.broker_amount = 0
            
            db.session.commit()
            log_action('تعديل عقد', {'id': contract.id, 'code': contract.code})
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'تم تعديل العقد بنجاح'})
            
            flash('تم تعديل العقد بنجاح', 'success')
            return redirect(url_for('contracts.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)}), 400
            flash(f'خطأ: {str(e)}', 'error')
    
    return render_template('contracts/edit.html', contract=contract)

@bp.route('/<string:id>/delete', methods=['POST'])
def delete(id):
    """حذف العقد"""
    try:
        contract = Contract.query.get_or_404(id)
        
        if contract.project_id != g.project.id:
            return jsonify({'success': False, 'message': 'العقد غير موجود'}), 404
        
        # التحقق من وجود أقساط
        has_installments = Installment.query.filter_by(unit_id=contract.unit_id).count() > 0 if contract.unit_id else False
        
        if has_installments:
            return jsonify({'success': False, 'message': 'لا يمكن حذف عقد له أقساط'}), 400
        
        # إعادة الوحدة للحالة المتاحة
        if contract.unit:
            contract.unit.status = 'متاحة'
        
        # حذف العقد
        db.session.delete(contract)
        db.session.commit()
        
        log_action('حذف عقد', {'id': id, 'code': contract.code})
        
        return jsonify({'success': True, 'message': 'تم حذف العقد بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/<string:id>/installments/generate', methods=['POST'])
def generate_installments(contract_id=None):
    """توليد أقساط العقد"""
    try:
        # إما من معامل الدالة أو من الطلب
        if not contract_id:
            contract_id = request.form.get('contract_id')
        
        contract = Contract.query.get_or_404(contract_id)
        
        if contract.project_id != g.project.id:
            return jsonify({'success': False, 'message': 'العقد غير موجود'}), 404
        
        # الحصول على بيانات الأقساط
        installment_type = request.form.get('installment_type', 'شهري')
        years = int(request.form.get('years', 1))
        extra_annual = int(request.form.get('extra_annual', 0))
        annual_payment = Decimal(request.form.get('annual_payment', 0))
        
        # حساب عدد الأقساط
        if installment_type == 'شهري':
            installments_per_year = 12
        elif installment_type == 'ربع سنوي':
            installments_per_year = 4
        elif installment_type == 'نصف سنوي':
            installments_per_year = 2
        else:  # سنوي
            installments_per_year = 1
        
        total_installments = installments_per_year * years
        
        # حساب المبلغ المتبقي بعد المقدم
        remaining = contract.total_price - contract.down_payment
        
        # خصم الدفعات السنوية من المتبقي
        extra_total = extra_annual * annual_payment
        remaining_after_extra = remaining - extra_total
        
        # حساب قيمة القسط العادي
        installment_amount = remaining_after_extra / total_installments
        
        # حذف الأقساط القديمة إن وجدت
        Installment.query.filter_by(contract_id=contract.id).delete()
        
        # إنشاء الأقساط الجديدة
        start_date = contract.start_date
        
        for i in range(total_installments):
            # حساب تاريخ الاستحقاق
            if installment_type == 'شهري':
                due_date = start_date + timedelta(days=30 * (i + 1))
            elif installment_type == 'ربع سنوي':
                due_date = start_date + timedelta(days=90 * (i + 1))
            elif installment_type == 'نصف سنوي':
                due_date = start_date + timedelta(days=180 * (i + 1))
            else:  # سنوي
                due_date = start_date + timedelta(days=365 * (i + 1))
            
            installment = Installment(
                id=generate_uid('INS'),
                project_id=g.project.id,
                contract_id=contract.id,
                unit_id=contract.unit_id,
                customer_id=contract.customer_id,
                installment_number=i + 1,
                amount=installment_amount,
                original_amount=installment_amount,
                due_date=due_date,
                status='مستحق'
            )
            
            db.session.add(installment)
        
        # إضافة الدفعات السنوية إن وجدت
        for i in range(extra_annual):
            due_date = start_date + timedelta(days=365 * (i + 1))
            
            installment = Installment(
                id=generate_uid('INS'),
                project_id=g.project.id,
                contract_id=contract.id,
                unit_id=contract.unit_id,
                customer_id=contract.customer_id,
                installment_number=total_installments + i + 1,
                amount=annual_payment,
                original_amount=annual_payment,
                due_date=due_date,
                status='مستحق',
                type='دفعة سنوية'
            )
            
            db.session.add(installment)
        
        # إضافة وديعة الصيانة كقسط أخير
        if contract.maintenance_deposit > 0:
            last_due_date = start_date + timedelta(days=365 * years)
            
            installment = Installment(
                id=generate_uid('INS'),
                project_id=g.project.id,
                contract_id=contract.id,
                unit_id=contract.unit_id,
                customer_id=contract.customer_id,
                installment_number=total_installments + extra_annual + 1,
                amount=contract.maintenance_deposit,
                original_amount=contract.maintenance_deposit,
                due_date=last_due_date,
                status='مستحق',
                type='وديعة صيانة'
            )
            
            db.session.add(installment)
        
        db.session.commit()
        
        log_action('توليد أقساط', {'contract_id': contract.id, 'count': total_installments + extra_annual})
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'تم توليد {total_installments + extra_annual} قسط بنجاح'
            })
        
        return redirect(url_for('contracts.view', id=contract.id))
        
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': str(e)}), 500
        flash(f'خطأ: {str(e)}', 'error')
        return redirect(url_for('contracts.view', id=contract_id))

@bp.route('/search')
def search():
    """البحث في العقود (AJAX)"""
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    query = Contract.query.filter_by(project_id=g.project.id)
    
    if q:
        search_term = f'%{q}%'
        query = query.join(Customer).join(Unit).filter(
            or_(
                Contract.code.ilike(search_term),
                Customer.name.ilike(search_term),
                Unit.name.ilike(search_term),
                Unit.code.ilike(search_term)
            )
        )
    
    query = query.order_by(Contract.created_at.desc())
    pagination = Pagination(query, page, per_page=20)
    
    contracts = []
    for contract in pagination.items:
        contracts.append({
            'id': contract.id,
            'code': contract.code,
            'customer_name': contract.customer.name if contract.customer else '',
            'unit_name': contract.unit.name if contract.unit else '',
            'unit_code': contract.unit.code if contract.unit else '',
            'total_price': float(contract.total_price),
            'down_payment': float(contract.down_payment),
            'remaining': float(contract.total_price - contract.down_payment),
            'status': contract.status,
            'start_date': contract.start_date.strftime('%Y-%m-%d')
        })
    
    return jsonify({
        'success': True,
        'contracts': contracts,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'total': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    })