from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.services.installment_service import InstallmentService
from app.services.contract_service import ContractService
from app.services.customer_service import CustomerService
from app.services.utils import paginate_query

bp = Blueprint('installments', __name__)


@bp.route('/')
def index():
    """قائمة الأقساط"""
    try:
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        contract_id = request.args.get('contract_id')
        customer_id = request.args.get('customer_id')
        search_term = request.args.get('search', '').strip()
        
        # الحصول على الأقساط
        if search_term:
            installments = InstallmentService.search_installments(search_term)
        elif status and contract_id:
            installments = InstallmentService.get_all_installments(status, contract_id)
        elif status:
            installments = InstallmentService.get_all_installments(status)
        elif contract_id:
            installments = InstallmentService.get_all_installments(contract_id=contract_id)
        elif customer_id:
            installments = CustomerService.get_customer_installments_by_status(customer_id, status) if status else []
        else:
            installments = InstallmentService.get_all_installments()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(installments, page, 20)
        
        return render_template('installments/index.html',
                             installments=pagination.items,
                             pagination=pagination,
                             current_status=status,
                             current_contract_id=contract_id,
                             current_customer_id=customer_id,
                             search_term=search_term)
    except Exception as e:
        flash(f'خطأ في تحميل قائمة الأقساط: {str(e)}', 'error')
        return render_template('installments/index.html',
                             installments=[],
                             pagination=None,
                             current_status=None,
                             current_contract_id=None,
                             current_customer_id=None,
                             search_term='')


@bp.route('/<id>')
def detail(id):
    """تفاصيل القسط"""
    try:
        installment = InstallmentService.get_installment_by_id(id)
        if not installment:
            flash('القسط غير موجود', 'error')
            return redirect(url_for('installments.index'))
        
        # إحصائيات القسط
        stats = InstallmentService.get_installment_statistics(id)
        
        return render_template('installments/detail.html',
                             installment=installment,
                             stats=stats)
    except Exception as e:
        flash(f'خطأ في تحميل تفاصيل القسط: {str(e)}', 'error')
        return redirect(url_for('installments.index'))


@bp.route('/<id>/pay', methods=['GET', 'POST'])
def pay(id):
    """دفع القسط"""
    try:
        installment = InstallmentService.get_installment_by_id(id)
        if not installment:
            flash('القسط غير موجود', 'error')
            return redirect(url_for('installments.index'))
        
        if request.method == 'POST':
            # دفع القسط
            payment_date = request.form.get('payment_date')
            payment_method = request.form.get('payment_method', '').strip()
            payment_reference = request.form.get('payment_reference', '').strip()
            notes = request.form.get('notes', '').strip()
            
            paid_installment = InstallmentService.pay_installment(
                id, payment_date, payment_method, payment_reference, notes
            )
            
            flash('تم دفع القسط بنجاح', 'success')
            return redirect(url_for('installments.detail', id=id))
        
        return render_template('installments/pay.html', installment=installment)
    except Exception as e:
        flash(f'خطأ في دفع القسط: {str(e)}', 'error')
        return redirect(url_for('installments.detail', id=id))


@bp.route('/<id>/cancel-payment', methods=['POST'])
def cancel_payment(id):
    """إلغاء دفع القسط"""
    try:
        installment = InstallmentService.cancel_payment(id)
        flash('تم إلغاء دفع القسط بنجاح', 'success')
        return redirect(url_for('installments.detail', id=id))
    except Exception as e:
        flash(f'خطأ في إلغاء دفع القسط: {str(e)}', 'error')
        return redirect(url_for('installments.detail', id=id))


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    """تعديل القسط"""
    try:
        installment = InstallmentService.get_installment_by_id(id)
        if not installment:
            flash('القسط غير موجود', 'error')
            return redirect(url_for('installments.index'))
        
        if request.method == 'POST':
            # تحديث القسط
            updated_installment = InstallmentService.update_installment(id,
                installment_number=request.form.get('installment_number', '').strip(),
                amount=request.form.get('amount'),
                due_date=request.form.get('due_date'),
                payment_date=request.form.get('payment_date') or None,
                status=request.form.get('status', 'معلق'),
                payment_method=request.form.get('payment_method', '').strip() or None,
                payment_reference=request.form.get('payment_reference', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None
            )
            
            flash('تم تحديث القسط بنجاح', 'success')
            return redirect(url_for('installments.detail', id=id))
        
        return render_template('installments/edit.html', installment=installment)
    except Exception as e:
        flash(f'خطأ في تحديث القسط: {str(e)}', 'error')
        return redirect(url_for('installments.detail', id=id))


@bp.route('/<id>/delete', methods=['POST'])
def delete(id):
    """حذف القسط"""
    try:
        success = InstallmentService.delete_installment(id)
        if success:
            flash('تم حذف القسط بنجاح', 'success')
        else:
            flash('فشل في حذف القسط', 'error')
    except Exception as e:
        flash(f'خطأ في حذف القسط: {str(e)}', 'error')
    
    return redirect(url_for('installments.index'))


@bp.route('/pending')
def pending():
    """الأقساط المعلقة"""
    try:
        contract_id = request.args.get('contract_id')
        installments = InstallmentService.get_pending_installments(contract_id)
        
        return render_template('installments/pending.html', installments=installments)
    except Exception as e:
        flash(f'خطأ في تحميل الأقساط المعلقة: {str(e)}', 'error')
        return render_template('installments/pending.html', installments=[])


@bp.route('/paid')
def paid():
    """الأقساط المدفوعة"""
    try:
        contract_id = request.args.get('contract_id')
        installments = InstallmentService.get_paid_installments(contract_id)
        
        return render_template('installments/paid.html', installments=installments)
    except Exception as e:
        flash(f'خطأ في تحميل الأقساط المدفوعة: {str(e)}', 'error')
        return render_template('installments/paid.html', installments=[])


@bp.route('/overdue')
def overdue():
    """الأقساط المتأخرة"""
    try:
        contract_id = request.args.get('contract_id')
        installments = InstallmentService.get_overdue_installments(contract_id)
        
        return render_template('installments/overdue.html', installments=installments)
    except Exception as e:
        flash(f'خطأ في تحميل الأقساط المتأخرة: {str(e)}', 'error')
        return render_template('installments/overdue.html', installments=[])


@bp.route('/upcoming')
def upcoming():
    """الأقساط القادمة"""
    try:
        days_ahead = request.args.get('days_ahead', 30, type=int)
        contract_id = request.args.get('contract_id')
        installments = InstallmentService.get_upcoming_installments(days_ahead, contract_id)
        
        return render_template('installments/upcoming.html', installments=installments, days_ahead=days_ahead)
    except Exception as e:
        flash(f'خطأ في تحميل الأقساط القادمة: {str(e)}', 'error')
        return render_template('installments/upcoming.html', installments=[], days_ahead=30)


@bp.route('/by-date-range')
def by_date_range():
    """الأقساط في نطاق تاريخ معين"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        
        if not all([start_date, end_date]):
            flash('نطاق التاريخ مطلوب', 'error')
            return redirect(url_for('installments.index'))
        
        installments = InstallmentService.get_installments_by_date_range(start_date, end_date, status)
        
        return render_template('installments/by_date_range.html', installments=installments, start_date=start_date, end_date=end_date, status=status)
    except Exception as e:
        flash(f'خطأ في تحميل الأقساط حسب التاريخ: {str(e)}', 'error')
        return render_template('installments/by_date_range.html', installments=[], start_date='', end_date='', status='')


@bp.route('/by-payment-date-range')
def by_payment_date_range():
    """الأقساط المدفوعة في نطاق تاريخ معين"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not all([start_date, end_date]):
            flash('نطاق التاريخ مطلوب', 'error')
            return redirect(url_for('installments.index'))
        
        installments = InstallmentService.get_installments_by_payment_date_range(start_date, end_date)
        
        return render_template('installments/by_payment_date_range.html', installments=installments, start_date=start_date, end_date=end_date)
    except Exception as e:
        flash(f'خطأ في تحميل الأقساط حسب تاريخ الدفع: {str(e)}', 'error')
        return render_template('installments/by_payment_date_range.html', installments=[], start_date='', end_date='')


@bp.route('/by-payment-method')
def by_payment_method():
    """الأقساط حسب طريقة الدفع"""
    try:
        payment_method = request.args.get('payment_method')
        
        if not payment_method:
            flash('طريقة الدفع مطلوبة', 'error')
            return redirect(url_for('installments.index'))
        
        installments = InstallmentService.get_installments_by_payment_method(payment_method)
        
        return render_template('installments/by_payment_method.html', installments=installments, payment_method=payment_method)
    except Exception as e:
        flash(f'خطأ في تحميل الأقساط حسب طريقة الدفع: {str(e)}', 'error')
        return render_template('installments/by_payment_method.html', installments=[], payment_method='')


@bp.route('/contract-summary/<contract_id>')
def contract_summary(contract_id):
    """ملخص أقساط العقد"""
    try:
        contract = ContractService.get_contract_by_id(contract_id)
        if not contract:
            flash('العقد غير موجود', 'error')
            return redirect(url_for('installments.index'))
        
        summary = InstallmentService.get_contract_installments_summary(contract_id)
        
        return render_template('installments/contract_summary.html', contract=contract, summary=summary)
    except Exception as e:
        flash(f'خطأ في تحميل ملخص أقساط العقد: {str(e)}', 'error')
        return redirect(url_for('installments.index'))


@bp.route('/customer-summary/<customer_id>')
def customer_summary(customer_id):
    """ملخص أقساط العميل"""
    try:
        customer = CustomerService.get_customer_by_id(customer_id)
        if not customer:
            flash('العميل غير موجود', 'error')
            return redirect(url_for('installments.index'))
        
        summary = InstallmentService.get_customer_installments_summary(customer_id)
        
        return render_template('installments/customer_summary.html', customer=customer, summary=summary)
    except Exception as e:
        flash(f'خطأ في تحميل ملخص أقساط العميل: {str(e)}', 'error')
        return redirect(url_for('installments.index'))


@bp.route('/update-overdue-status', methods=['POST'])
def update_overdue_status():
    """تحديث حالة الأقساط المتأخرة"""
    try:
        updated_count = InstallmentService.update_overdue_status()
        flash(f'تم تحديث {updated_count} قسط متأخر', 'success')
    except Exception as e:
        flash(f'خطأ في تحديث حالة الأقساط المتأخرة: {str(e)}', 'error')
    
    return redirect(url_for('installments.overdue'))