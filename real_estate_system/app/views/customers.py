from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.services.customer_service import CustomerService
from app.services.utils import paginate_query

bp = Blueprint('customers', __name__)


@bp.route('/')
def index():
    """قائمة العملاء"""
    try:
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        search_term = request.args.get('search', '').strip()
        
        # الحصول على العملاء
        if search_term:
            customers = CustomerService.search_customers(search_term)
        elif status:
            customers = CustomerService.get_all_customers(status)
        else:
            customers = CustomerService.get_all_customers()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(customers, page, 20)
        
        return render_template('customers/index.html',
                             customers=pagination.items,
                             pagination=pagination,
                             current_status=status,
                             search_term=search_term)
    except Exception as e:
        flash(f'خطأ في تحميل قائمة العملاء: {str(e)}', 'error')
        return render_template('customers/index.html',
                             customers=[],
                             pagination=None,
                             current_status=None,
                             search_term='')


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """إنشاء عميل جديد"""
    if request.method == 'POST':
        try:
            # التحقق من البيانات
            name = request.form.get('name', '').strip()
            if not name:
                flash('اسم العميل مطلوب', 'error')
                return render_template('customers/create.html')
            
            # إنشاء العميل
            customer = CustomerService.create_customer(
                name=name,
                code=request.form.get('code', '').strip() or None,
                phone=request.form.get('phone', '').strip() or None,
                national_id=request.form.get('national_id', '').strip() or None,
                address=request.form.get('address', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None
            )
            
            flash('تم إنشاء العميل بنجاح', 'success')
            return redirect(url_for('customers.detail', id=customer.id))
        except Exception as e:
            flash(f'خطأ في إنشاء العميل: {str(e)}', 'error')
    
    return render_template('customers/create.html')


@bp.route('/<id>')
def detail(id):
    """تفاصيل العميل"""
    try:
        customer = CustomerService.get_customer_by_id(id)
        if not customer:
            flash('العميل غير موجود', 'error')
            return redirect(url_for('customers.index'))
        
        # إحصائيات العميل
        stats = CustomerService.get_customer_statistics(id)
        
        # الملخص المالي
        financial_summary = CustomerService.get_customer_financial_summary(id)
        
        # العقود حسب الحالة
        contracts_by_status = {
            'نشط': CustomerService.get_customer_contracts_by_status(id, 'نشط'),
            'ملغي': CustomerService.get_customer_contracts_by_status(id, 'ملغي')
        }
        
        # الأقساط حسب الحالة
        installments_by_status = {
            'مدفوع': CustomerService.get_customer_installments_by_status(id, 'مدفوع'),
            'معلق': CustomerService.get_customer_installments_by_status(id, 'معلق'),
            'متأخر': CustomerService.get_customer_installments_by_status(id, 'متأخر')
        }
        
        # تاريخ المدفوعات
        payment_history = CustomerService.get_customer_payment_history(id)
        
        # الأقساط المتأخرة
        overdue_installments = CustomerService.get_customer_overdue_installments(id)
        
        # الأقساط القادمة
        next_installments = CustomerService.get_customer_next_installments(id)
        
        return render_template('customers/detail.html',
                             customer=customer,
                             stats=stats,
                             financial_summary=financial_summary,
                             contracts_by_status=contracts_by_status,
                             installments_by_status=installments_by_status,
                             payment_history=payment_history,
                             overdue_installments=overdue_installments,
                             next_installments=next_installments)
    except Exception as e:
        flash(f'خطأ في تحميل تفاصيل العميل: {str(e)}', 'error')
        return redirect(url_for('customers.index'))


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    """تعديل العميل"""
    try:
        customer = CustomerService.get_customer_by_id(id)
        if not customer:
            flash('العميل غير موجود', 'error')
            return redirect(url_for('customers.index'))
        
        if request.method == 'POST':
            # تحديث العميل
            updated_customer = CustomerService.update_customer(id,
                name=request.form.get('name', '').strip(),
                code=request.form.get('code', '').strip() or None,
                phone=request.form.get('phone', '').strip() or None,
                national_id=request.form.get('national_id', '').strip() or None,
                address=request.form.get('address', '').strip() or None,
                notes=request.form.get('notes', '').strip() or None,
                status=request.form.get('status', 'نشط')
            )
            
            flash('تم تحديث العميل بنجاح', 'success')
            return redirect(url_for('customers.detail', id=id))
        
        return render_template('customers/edit.html', customer=customer)
    except Exception as e:
        flash(f'خطأ في تحديث العميل: {str(e)}', 'error')
        return redirect(url_for('customers.detail', id=id))


@bp.route('/<id>/delete', methods=['POST'])
def delete(id):
    """حذف العميل"""
    try:
        success = CustomerService.delete_customer(id)
        if success:
            flash('تم حذف العميل بنجاح', 'success')
        else:
            flash('فشل في حذف العميل', 'error')
    except Exception as e:
        flash(f'خطأ في حذف العميل: {str(e)}', 'error')
    
    return redirect(url_for('customers.index'))


@bp.route('/<id>/contracts')
def contracts(id):
    """عقود العميل"""
    try:
        customer = CustomerService.get_customer_by_id(id)
        if not customer:
            flash('العميل غير موجود', 'error')
            return redirect(url_for('customers.index'))
        
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        
        # الحصول على العقود
        if status:
            contracts = CustomerService.get_customer_contracts_by_status(id, status)
        else:
            contracts = customer.contracts.all()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(contracts, page, 20)
        
        return render_template('customers/contracts.html',
                             customer=customer,
                             contracts=pagination.items,
                             pagination=pagination,
                             current_status=status)
    except Exception as e:
        flash(f'خطأ في تحميل عقود العميل: {str(e)}', 'error')
        return redirect(url_for('customers.detail', id=id))


@bp.route('/<id>/installments')
def installments(id):
    """أقساط العميل"""
    try:
        customer = CustomerService.get_customer_by_id(id)
        if not customer:
            flash('العميل غير موجود', 'error')
            return redirect(url_for('customers.index'))
        
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        
        # الحصول على الأقساط
        if status:
            installments = CustomerService.get_customer_installments_by_status(id, status)
        else:
            installments = customer.installments.all()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(installments, page, 20)
        
        return render_template('customers/installments.html',
                             customer=customer,
                             installments=pagination.items,
                             pagination=pagination,
                             current_status=status)
    except Exception as e:
        flash(f'خطأ في تحميل أقساط العميل: {str(e)}', 'error')
        return redirect(url_for('customers.detail', id=id))


@bp.route('/<id>/financial')
def financial(id):
    """الملخص المالي للعميل"""
    try:
        customer = CustomerService.get_customer_by_id(id)
        if not customer:
            flash('العميل غير موجود', 'error')
            return redirect(url_for('customers.index'))
        
        # الملخص المالي
        financial_summary = CustomerService.get_customer_financial_summary(id)
        
        # تاريخ المدفوعات
        payment_history = CustomerService.get_customer_payment_history(id)
        
        return render_template('customers/financial.html',
                             customer=customer,
                             financial_summary=financial_summary,
                             payment_history=payment_history)
    except Exception as e:
        flash(f'خطأ في تحميل الملخص المالي: {str(e)}', 'error')
        return redirect(url_for('customers.detail', id=id))


@bp.route('/top')
def top():
    """أفضل العملاء"""
    try:
        limit = request.args.get('limit', 10, type=int)
        top_customers = CustomerService.get_top_customers_by_value(limit)
        
        return render_template('customers/top.html', top_customers=top_customers)
    except Exception as e:
        flash(f'خطأ في تحميل أفضل العملاء: {str(e)}', 'error')
        return render_template('customers/top.html', top_customers=[])


@bp.route('/overdue')
def overdue():
    """العملاء الذين لديهم أقساط متأخرة"""
    try:
        customers_with_overdue = CustomerService.get_customers_with_overdue_payments()
        
        return render_template('customers/overdue.html', customers_with_overdue=customers_with_overdue)
    except Exception as e:
        flash(f'خطأ في تحميل العملاء المتأخرين: {str(e)}', 'error')
        return render_template('customers/overdue.html', customers_with_overdue=[])