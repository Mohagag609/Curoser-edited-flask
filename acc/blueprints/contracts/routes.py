from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g, send_file
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import or_, and_, func
from acc.extensions import db
from acc.models.contract import Contract, ContractStatus, PaymentType, InstallmentPeriod
from acc.models.installment import Installment, InstallmentStatus
from acc.models import Customer, Unit, Broker, Project
from acc.services.utils import generate_uid, format_currency
from acc.services.project_selection import project_required
from acc.services.auth import login_required
from acc.services.audit import log_action
import logging
from flask import current_app as app

bp = Blueprint('contracts', __name__)

@bp.route('/')
@project_required
def index():
    """قائمة العقود"""
    try:
        # الحصول على معاملات الفلترة
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        payment_type = request.args.get('payment_type', '')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # بناء الاستعلام
        query = Contract.query.filter_by(project_id=g.project.id)
        
        # تطبيق الفلاتر
        if search:
            query = query.join(Customer).join(Unit).filter(
                or_(
                    Contract.code.ilike(f'%{search}%'),
                    Customer.name.ilike(f'%{search}%'),
                    Customer.phone.ilike(f'%{search}%'),
                    Unit.name.ilike(f'%{search}%')
                )
            )
        
        if status:
            try:
                status_enum = ContractStatus[status.upper()]
                query = query.filter(Contract.status == status_enum)
            except:
                pass
        
        if payment_type:
            try:
                payment_enum = PaymentType[payment_type.upper()]
                query = query.filter(Contract.payment_type == payment_enum)
            except:
                pass
        
        if from_date:
            query = query.filter(Contract.contract_date >= from_date)
        
        if to_date:
            query = query.filter(Contract.contract_date <= to_date)
        
        # الترتيب
        query = query.order_by(Contract.created_at.desc())
        
        # التصفح
        per_page = 20
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        contracts = pagination.items
        
        # حساب الإحصائيات
        stats = calculate_stats()
        
        return render_template('contracts/index.html',
            contracts=contracts,
            pagination=pagination,
            stats=stats,
            format_currency=format_currency
        )
        
    except Exception as e:
        app.logger.error(f'Error in contracts index: {str(e)}')
        flash('حدث خطأ في تحميل العقود', 'error')
        return redirect(url_for('dashboard.index'))

@bp.route('/create', methods=['GET', 'POST'])
@project_required
def create():
    """إنشاء عقد جديد"""
    if request.method == 'POST':
        try:
            # التحقق من البيانات المطلوبة
            required_fields = ['code', 'customer_id', 'unit_id', 'unit_price', 'payment_type', 'contract_date']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'الحقل {field} مطلوب', 'error')
                    return redirect(request.url)
            
            # التحقق من أن الوحدة متاحة
            unit = Unit.query.get_or_404(request.form['unit_id'])
            if unit.status != 'متاحة':
                flash('الوحدة غير متاحة', 'error')
                return redirect(request.url)
            
            # إنشاء العقد
            contract = Contract(
                id=generate_uid('CNT'),
                project_id=g.project.id,
                code=request.form['code'],
                customer_id=request.form['customer_id'],
                unit_id=request.form['unit_id'],
                unit_price=Decimal(request.form['unit_price']),
                discount_percent=Decimal(request.form.get('discount_percent', 0)),
                payment_type=PaymentType[request.form['payment_type'].upper()],
                contract_date=datetime.strptime(request.form['contract_date'], '%Y-%m-%d').date(),
                down_payment_percent=Decimal(request.form.get('down_payment_percent', 0)),
                maintenance_deposit=Decimal(request.form.get('maintenance_deposit', 0)),
                broker_id=request.form.get('broker_id') or None,
                broker_percent=Decimal(request.form.get('broker_percent', 0)),
                status=ContractStatus.DRAFT,
                created_by='system' if not hasattr(g, 'user') else g.user.id
            )
            
            # حساب الأسعار
            contract.calculate_prices()
            
            # إعدادات الأقساط
            if contract.payment_type in [PaymentType.INSTALLMENT, PaymentType.MIXED]:
                contract.installment_type = InstallmentPeriod[request.form.get('installment_type', 'MONTHLY').upper()]
                contract.installment_count = int(request.form.get('installment_count', 0))
                contract.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
                contract.extra_annual_payments = int(request.form.get('extra_annual_payments', 0))
                contract.annual_payment_value = Decimal(request.form.get('annual_payment_value', 0))
            
            # تحديث حالة الوحدة
            unit.status = 'محجوزة'
            
            # حفظ في قاعدة البيانات
            db.session.add(contract)
            db.session.commit()
            
            # توليد الأقساط إذا لزم الأمر
            if contract.payment_type in [PaymentType.INSTALLMENT, PaymentType.MIXED]:
                contract.generate_installments()
            
            # تسجيل الحدث
            log_action('إنشاء عقد', {
                'contract_id': contract.id,
                'code': contract.code,
                'customer': contract.customer.name,
                'unit': contract.unit.name,
                'value': float(contract.final_price)
            })
            
            flash('تم إنشاء العقد بنجاح', 'success')
            
            # طباعة إذا طُلب ذلك
            if request.form.get('print_after_save'):
                return redirect(url_for('contracts.print', id=contract.id))
            
            return redirect(url_for('contracts.view', id=contract.id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error creating contract: {str(e)}')
            flash(f'خطأ في إنشاء العقد: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request
    try:
        # البيانات المطلوبة للنموذج
        customers = Customer.query.filter_by(project_id=g.project.id).order_by(Customer.name).all()
        available_units = Unit.query.filter_by(project_id=g.project.id, status='متاحة').order_by(Unit.name).all()
        brokers = Broker.query.filter_by(project_id=g.project.id, status='نشط').order_by(Broker.name).all()
        
        # اقتراح رقم العقد
        last_contract = Contract.query.filter_by(project_id=g.project.id).order_by(Contract.code.desc()).first()
        if last_contract:
            # استخراج الرقم من آخر عقد وزيادته
            try:
                last_number = int(last_contract.code.split('-')[-1])
                suggested_code = f"CNT-{g.project.code}-{last_number + 1:04d}"
            except:
                suggested_code = f"CNT-{g.project.code}-0001"
        else:
            suggested_code = f"CNT-{g.project.code}-0001"
        
        return render_template('contracts/create.html',
            customers=customers,
            available_units=available_units,
            brokers=brokers,
            suggested_code=suggested_code,
            today=date.today().strftime('%Y-%m-%d'),
            format_currency=format_currency
        )
        
    except Exception as e:
        app.logger.error(f'Error loading create form: {str(e)}')
        flash('حدث خطأ في تحميل النموذج', 'error')
        return redirect(url_for('contracts.index'))

@bp.route('/<string:id>')
@project_required
def view(id):
    """عرض تفاصيل العقد"""
    try:
        contract = Contract.query.get_or_404(id)
        
        # التحقق من أن العقد ينتمي للمشروع الحالي
        if contract.project_id != g.project.id:
            flash('العقد غير موجود', 'error')
            return redirect(url_for('contracts.index'))
        
        # جلب الأقساط
        installments = contract.installments.order_by(Installment.due_date).all()
        
        # حساب ملخص الأقساط
        installment_summary = {
            'total': len(installments),
            'paid': sum(1 for i in installments if i.status == InstallmentStatus.PAID),
            'pending': sum(1 for i in installments if i.status == InstallmentStatus.PENDING),
            'overdue': sum(1 for i in installments if i.is_overdue),
            'total_amount': sum(i.amount for i in installments),
            'paid_amount': sum(i.paid_amount for i in installments),
            'overdue_amount': sum(i.remaining_amount for i in installments if i.is_overdue)
        }
        
        return render_template('contracts/view.html',
            contract=contract,
            installments=installments,
            installment_summary=installment_summary,
            format_currency=format_currency
        )
        
    except Exception as e:
        app.logger.error(f'Error viewing contract {id}: {str(e)}')
        flash('حدث خطأ في عرض العقد', 'error')
        return redirect(url_for('contracts.index'))

@bp.route('/<string:id>/edit', methods=['GET', 'POST'])
@project_required
def edit(id):
    """تعديل العقد"""
    contract = Contract.query.get_or_404(id)
    
    # التحقق من أن العقد ينتمي للمشروع الحالي
    if contract.project_id != g.project.id:
        flash('العقد غير موجود', 'error')
        return redirect(url_for('contracts.index'))
    
    if request.method == 'POST':
        try:
            # تحديث البيانات
            contract.discount_percent = Decimal(request.form.get('discount_percent', 0))
            contract.down_payment_percent = Decimal(request.form.get('down_payment_percent', 0))
            contract.maintenance_deposit = Decimal(request.form.get('maintenance_deposit', 0))
            contract.broker_id = request.form.get('broker_id') or None
            contract.broker_percent = Decimal(request.form.get('broker_percent', 0))
            contract.notes = request.form.get('notes', '')
            
            # إعادة حساب الأسعار
            contract.calculate_prices()
            
            # حفظ التغييرات
            db.session.commit()
            
            # تسجيل الحدث
            log_action('تعديل عقد', {'contract_id': id, 'code': contract.code})
            
            flash('تم تحديث العقد بنجاح', 'success')
            return redirect(url_for('contracts.view', id=id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error editing contract {id}: {str(e)}')
            flash(f'خطأ في تحديث العقد: {str(e)}', 'error')
    
    # جلب البيانات للنموذج
    brokers = Broker.query.filter_by(project_id=g.project.id, status='نشط').order_by(Broker.name).all()
    
    return render_template('contracts/edit.html',
        contract=contract,
        brokers=brokers,
        format_currency=format_currency
    )

@bp.route('/<string:id>/delete', methods=['POST', 'DELETE'])
@project_required
def delete(id):
    """حذف العقد"""
    try:
        contract = Contract.query.get_or_404(id)
        
        # التحقق من أن العقد ينتمي للمشروع الحالي
        if contract.project_id != g.project.id:
            return jsonify({'success': False, 'message': 'العقد غير موجود'}), 404
        
        # التحقق من إمكانية الحذف
        if contract.status != ContractStatus.DRAFT:
            return jsonify({'success': False, 'message': 'لا يمكن حذف عقد غير مسودة'}), 400
        
        # التحقق من عدم وجود دفعات
        if contract.paid_amount > 0:
            return jsonify({'success': False, 'message': 'لا يمكن حذف عقد له دفعات'}), 400
        
        # إعادة الوحدة للحالة المتاحة
        if contract.unit:
            contract.unit.status = 'متاحة'
        
        # حذف العقد (سيحذف الأقساط تلقائياً بسبب cascade)
        db.session.delete(contract)
        db.session.commit()
        
        # تسجيل الحدث
        log_action('حذف عقد', {'id': id, 'code': contract.code})
        
        return jsonify({'success': True, 'message': 'تم حذف العقد بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting contract {id}: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ في حذف العقد: {str(e)}'}), 500

@bp.route('/<string:id>/activate', methods=['POST'])
@project_required
def activate(id):
    """تفعيل العقد"""
    try:
        contract = Contract.query.get_or_404(id)
        
        if contract.project_id != g.project.id:
            return jsonify({'success': False, 'message': 'العقد غير موجود'}), 404
        
        # التحقق من إمكانية التفعيل
        if contract.status != ContractStatus.DRAFT:
            return jsonify({'success': False, 'message': 'العقد مفعل بالفعل'}), 400
        
        # تفعيل العقد
        contract.status = ContractStatus.ACTIVE
        contract.approved_by = 'system' if not hasattr(g, 'user') else g.user.id
        contract.approval_date = datetime.now()
        
        # تحديث حالة الوحدة
        if contract.unit:
            contract.unit.status = 'مباعة'
        
        db.session.commit()
        
        # تسجيل الحدث
        log_action('تفعيل عقد', {'contract_id': id, 'code': contract.code})
        
        return jsonify({'success': True, 'message': 'تم تفعيل العقد بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error activating contract {id}: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/<string:id>/print')
@project_required
def print_contract(id):
    """طباعة العقد"""
    try:
        contract = Contract.query.get_or_404(id)
        
        if contract.project_id != g.project.id:
            flash('العقد غير موجود', 'error')
            return redirect(url_for('contracts.index'))
        
        # إنشاء ملف PDF للعقد
        # TODO: implement PDF generation
        
        return render_template('contracts/print.html',
            contract=contract,
            format_currency=format_currency
        )
        
    except Exception as e:
        app.logger.error(f'Error printing contract {id}: {str(e)}')
        flash('حدث خطأ في طباعة العقد', 'error')
        return redirect(url_for('contracts.view', id=id))

@bp.route('/export')
@project_required
def export():
    """تصدير العقود"""
    try:
        # TODO: implement export functionality
        flash('وظيفة التصدير قيد التطوير', 'info')
        return redirect(url_for('contracts.index'))
        
    except Exception as e:
        app.logger.error(f'Error exporting contracts: {str(e)}')
        flash('حدث خطأ في التصدير', 'error')
        return redirect(url_for('contracts.index'))

def calculate_stats():
    """حساب إحصائيات العقود"""
    try:
        # إجمالي العقود
        total_contracts = Contract.query.filter_by(project_id=g.project.id).count()
        
        # العقود النشطة
        active_contracts = Contract.query.filter_by(
            project_id=g.project.id,
            status=ContractStatus.ACTIVE
        ).count()
        
        # النسبة المئوية للعقود النشطة
        active_percentage = round((active_contracts / total_contracts * 100) if total_contracts > 0 else 0, 1)
        
        # إجمالي قيمة العقود
        total_value = db.session.query(func.sum(Contract.final_price)).filter_by(
            project_id=g.project.id
        ).scalar() or 0
        
        # المبلغ المحصل
        # TODO: حساب المبلغ المحصل من جدول المدفوعات
        collected_amount = 0
        
        # نسبة التحصيل
        collection_rate = round((collected_amount / total_value * 100) if total_value > 0 else 0, 1)
        
        # الأقساط المتأخرة
        overdue_installments = 0
        overdue_amount = 0
        
        # حساب الأقساط المتأخرة
        contracts = Contract.query.filter_by(project_id=g.project.id).all()
        for contract in contracts:
            for installment in contract.installments:
                if installment.is_overdue:
                    overdue_installments += 1
                    overdue_amount += installment.remaining_amount
        
        return {
            'total_contracts': total_contracts,
            'active_contracts': active_contracts,
            'active_percentage': active_percentage,
            'total_value': float(total_value),
            'collected_amount': float(collected_amount),
            'collection_rate': collection_rate,
            'overdue_installments': overdue_installments,
            'overdue_amount': float(overdue_amount)
        }
        
    except Exception as e:
        app.logger.error(f'Error calculating stats: {str(e)}')
        return {
            'total_contracts': 0,
            'active_contracts': 0,
            'active_percentage': 0,
            'total_value': 0,
            'collected_amount': 0,
            'collection_rate': 0,
            'overdue_installments': 0,
            'overdue_amount': 0
        }