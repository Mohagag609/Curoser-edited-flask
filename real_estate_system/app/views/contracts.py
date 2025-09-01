from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.services.contract_service import ContractService
from app.services.customer_service import CustomerService
from app.services.unit_service import UnitService
from app.services.installment_service import InstallmentService
from app.services.utils import paginate_query

bp = Blueprint('contracts', __name__)


@bp.route('/')
def index():
    """قائمة العقود"""
    try:
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        project_id = request.args.get('project_id')
        search_term = request.args.get('search', '').strip()
        
        # الحصول على العقود
        if search_term:
            contracts = ContractService.search_contracts(search_term)
        elif status and project_id:
            contracts = ContractService.get_all_contracts(status, project_id)
        elif status:
            contracts = ContractService.get_all_contracts(status)
        elif project_id:
            contracts = ContractService.get_all_contracts(project_id=project_id)
        else:
            contracts = ContractService.get_all_contracts()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(contracts, page, 20)
        
        return render_template('contracts/index.html',
                             contracts=pagination.items,
                             pagination=pagination,
                             current_status=status,
                             current_project_id=project_id,
                             search_term=search_term)
    except Exception as e:
        flash(f'خطأ في تحميل قائمة العقود: {str(e)}', 'error')
        return render_template('contracts/index.html',
                             contracts=[],
                             pagination=None,
                             current_status=None,
                             current_project_id=None,
                             search_term='')


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """إنشاء عقد جديد"""
    if request.method == 'POST':
        try:
            # التحقق من البيانات
            unit_id = request.form.get('unit_id')
            customer_id = request.form.get('customer_id')
            total_price = request.form.get('total_price')
            
            if not all([unit_id, customer_id, total_price]):
                flash('البيانات المطلوبة غير مكتملة', 'error')
                return render_template('contracts/create.html')
            
            # إنشاء العقد
            contract = ContractService.create_contract(
                unit_id=unit_id,
                customer_id=customer_id,
                total_price=total_price,
                down_payment=request.form.get('down_payment', 0) or 0,
                discount_amount=request.form.get('discount_amount', 0) or 0,
                maintenance_deposit=request.form.get('maintenance_deposit', 0) or 0,
                broker_name=request.form.get('broker_name', '').strip() or None,
                broker_percent=request.form.get('broker_percent', 0) or 0,
                broker_amount=request.form.get('broker_amount', 0) or 0,
                commission_safe_id=request.form.get('commission_safe_id') or None,
                contract_date=request.form.get('contract_date') or None,
                notes=request.form.get('notes', '').strip() or None,
                project_id=request.form.get('project_id') or None
            )
            
            flash('تم إنشاء العقد بنجاح', 'success')
            return redirect(url_for('contracts.detail', id=contract.id))
        except Exception as e:
            flash(f'خطأ في إنشاء العقد: {str(e)}', 'error')
    
    # الحصول على البيانات للقوائم المنسدلة
    customers = CustomerService.get_active_customers()
    units = UnitService.get_available_units()
    
    return render_template('contracts/create.html', customers=customers, units=units)


@bp.route('/<id>')
def detail(id):
    """تفاصيل العقد"""
    try:
        contract = ContractService.get_contract_by_id(id)
        if not contract:
            flash('العقد غير موجود', 'error')
            return redirect(url_for('contracts.index'))
        
        # إحصائيات العقد
        stats = ContractService.get_contract_statistics(id)
        
        # الأقساط حسب الحالة
        installments_by_status = {
            'مدفوع': ContractService.get_contract_installments_by_status(id, 'مدفوع'),
            'معلق': ContractService.get_contract_installments_by_status(id, 'معلق'),
            'متأخر': ContractService.get_contract_installments_by_status(id, 'متأخر')
        }
        
        # القسط التالي
        next_installment = ContractService.get_contract_next_installment(id)
        
        # الأقساط المتأخرة
        overdue_installments = ContractService.get_contract_overdue_installments(id)
        
        return render_template('contracts/detail.html',
                             contract=contract,
                             stats=stats,
                             installments_by_status=installments_by_status,
                             next_installment=next_installment,
                             overdue_installments=overdue_installments)
    except Exception as e:
        flash(f'خطأ في تحميل تفاصيل العقد: {str(e)}', 'error')
        return redirect(url_for('contracts.index'))


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    """تعديل العقد"""
    try:
        contract = ContractService.get_contract_by_id(id)
        if not contract:
            flash('العقد غير موجود', 'error')
            return redirect(url_for('contracts.index'))
        
        if request.method == 'POST':
            # تحديث العقد
            updated_contract = ContractService.update_contract(id,
                total_price=request.form.get('total_price'),
                down_payment=request.form.get('down_payment', 0) or 0,
                discount_amount=request.form.get('discount_amount', 0) or 0,
                maintenance_deposit=request.form.get('maintenance_deposit', 0) or 0,
                broker_name=request.form.get('broker_name', '').strip() or None,
                broker_percent=request.form.get('broker_percent', 0) or 0,
                broker_amount=request.form.get('broker_amount', 0) or 0,
                commission_safe_id=request.form.get('commission_safe_id') or None,
                contract_date=request.form.get('contract_date') or None,
                notes=request.form.get('notes', '').strip() or None,
                status=request.form.get('status', 'نشط')
            )
            
            flash('تم تحديث العقد بنجاح', 'success')
            return redirect(url_for('contracts.detail', id=id))
        
        # الحصول على البيانات للقوائم المنسدلة
        customers = CustomerService.get_active_customers()
        units = UnitService.get_all_units()
        
        return render_template('contracts/edit.html', contract=contract, customers=customers, units=units)
    except Exception as e:
        flash(f'خطأ في تحديث العقد: {str(e)}', 'error')
        return redirect(url_for('contracts.detail', id=id))


@bp.route('/<id>/delete', methods=['POST'])
def delete(id):
    """حذف العقد"""
    try:
        success = ContractService.delete_contract(id)
        if success:
            flash('تم حذف العقد بنجاح', 'success')
        else:
            flash('فشل في حذف العقد', 'error')
    except Exception as e:
        flash(f'خطأ في حذف العقد: {str(e)}', 'error')
    
    return redirect(url_for('contracts.index'))


@bp.route('/<id>/cancel', methods=['POST'])
def cancel(id):
    """إلغاء العقد"""
    try:
        reason = request.form.get('reason', '').strip()
        success = ContractService.cancel_contract(id, reason)
        if success:
            flash('تم إلغاء العقد بنجاح', 'success')
        else:
            flash('فشل في إلغاء العقد', 'error')
    except Exception as e:
        flash(f'خطأ في إلغاء العقد: {str(e)}', 'error')
    
    return redirect(url_for('contracts.detail', id=id))


@bp.route('/<id>/installments')
def installments(id):
    """أقساط العقد"""
    try:
        contract = ContractService.get_contract_by_id(id)
        if not contract:
            flash('العقد غير موجود', 'error')
            return redirect(url_for('contracts.index'))
        
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        
        # الحصول على الأقساط
        if status:
            installments = ContractService.get_contract_installments_by_status(id, status)
        else:
            installments = contract.installments.all()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(installments, page, 20)
        
        return render_template('contracts/installments.html',
                             contract=contract,
                             installments=pagination.items,
                             pagination=pagination,
                             current_status=status)
    except Exception as e:
        flash(f'خطأ في تحميل أقساط العقد: {str(e)}', 'error')
        return redirect(url_for('contracts.detail', id=id))


@bp.route('/<id>/create-installments', methods=['GET', 'POST'])
def create_installments(id):
    """إنشاء أقساط للعقد"""
    try:
        contract = ContractService.get_contract_by_id(id)
        if not contract:
            flash('العقد غير موجود', 'error')
            return redirect(url_for('contracts.index'))
        
        if request.method == 'POST':
            number_of_installments = request.form.get('number_of_installments', type=int)
            start_date = request.form.get('start_date')
            installment_interval = request.form.get('installment_interval', 30, type=int)
            
            if not number_of_installments:
                flash('عدد الأقساط مطلوب', 'error')
                return render_template('contracts/create_installments.html', contract=contract)
            
            # إنشاء الأقساط
            installments = ContractService.create_installments(
                id, number_of_installments, start_date, installment_interval
            )
            
            flash(f'تم إنشاء {len(installments)} قسط بنجاح', 'success')
            return redirect(url_for('contracts.installments', id=id))
        
        return render_template('contracts/create_installments.html', contract=contract)
    except Exception as e:
        flash(f'خطأ في إنشاء الأقساط: {str(e)}', 'error')
        return redirect(url_for('contracts.detail', id=id))


@bp.route('/<id>/financial')
def financial(id):
    """الملخص المالي للعقد"""
    try:
        contract = ContractService.get_contract_by_id(id)
        if not contract:
            flash('العقد غير موجود', 'error')
            return redirect(url_for('contracts.index'))
        
        # إحصائيات العقد
        stats = ContractService.get_contract_statistics(id)
        
        # الأقساط المدفوعة
        paid_installments = ContractService.get_contract_installments_by_status(id, 'مدفوع')
        
        # الأقساط المعلقة
        pending_installments = ContractService.get_contract_installments_by_status(id, 'معلق')
        
        return render_template('contracts/financial.html',
                             contract=contract,
                             stats=stats,
                             paid_installments=paid_installments,
                             pending_installments=pending_installments)
    except Exception as e:
        flash(f'خطأ في تحميل الملخص المالي: {str(e)}', 'error')
        return redirect(url_for('contracts.detail', id=id))


@bp.route('/overdue')
def overdue():
    """العقود التي لديها أقساط متأخرة"""
    try:
        contracts_with_overdue = ContractService.get_contracts_with_overdue_installments()
        
        return render_template('contracts/overdue.html', contracts_with_overdue=contracts_with_overdue)
    except Exception as e:
        flash(f'خطأ في تحميل العقود المتأخرة: {str(e)}', 'error')
        return render_template('contracts/overdue.html', contracts_with_overdue=[])


@bp.route('/financial-summary')
def financial_summary():
    """الملخص المالي للعقود"""
    try:
        project_id = request.args.get('project_id')
        financial_summary = ContractService.get_contracts_financial_summary(project_id)
        
        return render_template('contracts/financial_summary.html', financial_summary=financial_summary)
    except Exception as e:
        flash(f'خطأ في تحميل الملخص المالي: {str(e)}', 'error')
        return render_template('contracts/financial_summary.html', financial_summary={})