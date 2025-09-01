from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.services.treasury_service import TreasuryService
from app.services.project_service import ProjectService
from app.services.utils import paginate_query

bp = Blueprint('treasury', __name__)


@bp.route('/')
def index():
    """قائمة الخزائن"""
    try:
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        project_id = request.args.get('project_id')
        search_term = request.args.get('search', '').strip()
        
        # الحصول على الخزائن
        if search_term:
            safes = TreasuryService.search_safes(search_term)
        elif status and project_id:
            safes = TreasuryService.get_all_safes(project_id, status)
        elif status:
            safes = TreasuryService.get_all_safes(status=status)
        elif project_id:
            safes = TreasuryService.get_all_safes(project_id=project_id)
        else:
            safes = TreasuryService.get_all_safes()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(safes, page, 20)
        
        return render_template('treasury/index.html',
                             safes=pagination.items,
                             pagination=pagination,
                             current_status=status,
                             current_project_id=project_id,
                             search_term=search_term)
    except Exception as e:
        flash(f'خطأ في تحميل قائمة الخزائن: {str(e)}', 'error')
        return render_template('treasury/index.html',
                             safes=[],
                             pagination=None,
                             current_status=None,
                             current_project_id=None,
                             search_term='')


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """إنشاء خزينة جديدة"""
    if request.method == 'POST':
        try:
            # التحقق من البيانات
            name = request.form.get('name', '').strip()
            if not name:
                flash('اسم الخزينة مطلوب', 'error')
                return render_template('treasury/create.html')
            
            # إنشاء الخزينة
            safe = TreasuryService.create_safe(
                name=name,
                code=request.form.get('code', '').strip() or None,
                description=request.form.get('description', '').strip() or None,
                initial_balance=request.form.get('initial_balance', 0) or 0,
                project_id=request.form.get('project_id') or None,
                is_main=request.form.get('is_main') == 'on'
            )
            
            flash('تم إنشاء الخزينة بنجاح', 'success')
            return redirect(url_for('treasury.detail', id=safe.id))
        except Exception as e:
            flash(f'خطأ في إنشاء الخزينة: {str(e)}', 'error')
    
    # الحصول على المشاريع للقائمة المنسدلة
    projects = ProjectService.get_active_projects()
    
    return render_template('treasury/create.html', projects=projects)


@bp.route('/<id>')
def detail(id):
    """تفاصيل الخزينة"""
    try:
        safe = TreasuryService.get_safe_by_id(id)
        if not safe:
            flash('الخزينة غير موجودة', 'error')
            return redirect(url_for('treasury.index'))
        
        # إحصائيات الخزينة
        stats = TreasuryService.get_safe_statistics(id)
        
        # السندات حسب النوع
        vouchers_by_type = {
            'إيراد': TreasuryService.get_safe_vouchers_by_type(id, 'إيراد'),
            'مصروف': TreasuryService.get_safe_vouchers_by_type(id, 'مصروف')
        }
        
        # التحويلات
        transfers = TreasuryService.get_safe_transfers(id)
        
        return render_template('treasury/detail.html',
                             safe=safe,
                             stats=stats,
                             vouchers_by_type=vouchers_by_type,
                             transfers=transfers)
    except Exception as e:
        flash(f'خطأ في تحميل تفاصيل الخزينة: {str(e)}', 'error')
        return redirect(url_for('treasury.index'))


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    """تعديل الخزينة"""
    try:
        safe = TreasuryService.get_safe_by_id(id)
        if not safe:
            flash('الخزينة غير موجودة', 'error')
            return redirect(url_for('treasury.index'))
        
        if request.method == 'POST':
            # تحديث الخزينة
            updated_safe = TreasuryService.update_safe(id,
                name=request.form.get('name', '').strip(),
                code=request.form.get('code', '').strip() or None,
                description=request.form.get('description', '').strip() or None,
                initial_balance=request.form.get('initial_balance', 0) or 0,
                project_id=request.form.get('project_id') or None,
                is_main=request.form.get('is_main') == 'on',
                status=request.form.get('status', 'نشط')
            )
            
            flash('تم تحديث الخزينة بنجاح', 'success')
            return redirect(url_for('treasury.detail', id=id))
        
        # الحصول على المشاريع للقائمة المنسدلة
        projects = ProjectService.get_active_projects()
        
        return render_template('treasury/edit.html', safe=safe, projects=projects)
    except Exception as e:
        flash(f'خطأ في تحديث الخزينة: {str(e)}', 'error')
        return redirect(url_for('treasury.detail', id=id))


@bp.route('/<id>/delete', methods=['POST'])
def delete(id):
    """حذف الخزينة"""
    try:
        success = TreasuryService.delete_safe(id)
        if success:
            flash('تم حذف الخزينة بنجاح', 'success')
        else:
            flash('فشل في حذف الخزينة', 'error')
    except Exception as e:
        flash(f'خطأ في حذف الخزينة: {str(e)}', 'error')
    
    return redirect(url_for('treasury.index'))


@bp.route('/<id>/add-income', methods=['GET', 'POST'])
def add_income(id):
    """إضافة إيراد للخزينة"""
    try:
        safe = TreasuryService.get_safe_by_id(id)
        if not safe:
            flash('الخزينة غير موجودة', 'error')
            return redirect(url_for('treasury.index'))
        
        if request.method == 'POST':
            # إضافة الإيراد
            amount = request.form.get('amount')
            description = request.form.get('description', '').strip()
            reference = request.form.get('reference', '').strip()
            voucher_date = request.form.get('voucher_date')
            
            if not amount:
                flash('المبلغ مطلوب', 'error')
                return render_template('treasury/add_income.html', safe=safe)
            
            voucher = TreasuryService.add_income(id, amount, description, reference, voucher_date)
            flash('تم إضافة الإيراد بنجاح', 'success')
            return redirect(url_for('treasury.detail', id=id))
        
        return render_template('treasury/add_income.html', safe=safe)
    except Exception as e:
        flash(f'خطأ في إضافة الإيراد: {str(e)}', 'error')
        return redirect(url_for('treasury.detail', id=id))


@bp.route('/<id>/add-expense', methods=['GET', 'POST'])
def add_expense(id):
    """إضافة مصروف للخزينة"""
    try:
        safe = TreasuryService.get_safe_by_id(id)
        if not safe:
            flash('الخزينة غير موجودة', 'error')
            return redirect(url_for('treasury.index'))
        
        if request.method == 'POST':
            # إضافة المصروف
            amount = request.form.get('amount')
            description = request.form.get('description', '').strip()
            reference = request.form.get('reference', '').strip()
            voucher_date = request.form.get('voucher_date')
            
            if not amount:
                flash('المبلغ مطلوب', 'error')
                return render_template('treasury/add_expense.html', safe=safe)
            
            voucher = TreasuryService.add_expense(id, amount, description, reference, voucher_date)
            flash('تم إضافة المصروف بنجاح', 'success')
            return redirect(url_for('treasury.detail', id=id))
        
        return render_template('treasury/add_expense.html', safe=safe)
    except Exception as e:
        flash(f'خطأ في إضافة المصروف: {str(e)}', 'error')
        return redirect(url_for('treasury.detail', id=id))


@bp.route('/<id>/transfer', methods=['GET', 'POST'])
def transfer(id):
    """تحويل من الخزينة"""
    try:
        safe = TreasuryService.get_safe_by_id(id)
        if not safe:
            flash('الخزينة غير موجودة', 'error')
            return redirect(url_for('treasury.index'))
        
        if request.method == 'POST':
            # التحويل
            to_safe_id = request.form.get('to_safe_id')
            amount = request.form.get('amount')
            description = request.form.get('description', '').strip()
            
            if not all([to_safe_id, amount]):
                flash('البيانات المطلوبة غير مكتملة', 'error')
                return render_template('treasury/transfer.html', safe=safe)
            
            transfer = TreasuryService.transfer_between_safes(id, to_safe_id, amount, description)
            flash('تم التحويل بنجاح', 'success')
            return redirect(url_for('treasury.detail', id=id))
        
        # الحصول على الخزائن الأخرى للقائمة المنسدلة
        other_safes = TreasuryService.get_all_safes()
        other_safes = [s for s in other_safes if s.id != id]
        
        return render_template('treasury/transfer.html', safe=safe, other_safes=other_safes)
    except Exception as e:
        flash(f'خطأ في التحويل: {str(e)}', 'error')
        return redirect(url_for('treasury.detail', id=id))


@bp.route('/<id>/vouchers')
def vouchers(id):
    """سندات الخزينة"""
    try:
        safe = TreasuryService.get_safe_by_id(id)
        if not safe:
            flash('الخزينة غير موجودة', 'error')
            return redirect(url_for('treasury.index'))
        
        page = request.args.get('page', 1, type=int)
        voucher_type = request.args.get('voucher_type')
        
        # الحصول على السندات
        if voucher_type:
            vouchers = TreasuryService.get_safe_vouchers_by_type(id, voucher_type)
        else:
            vouchers = safe.vouchers.all()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(vouchers, page, 20)
        
        return render_template('treasury/vouchers.html',
                             safe=safe,
                             vouchers=pagination.items,
                             pagination=pagination,
                             current_voucher_type=voucher_type)
    except Exception as e:
        flash(f'خطأ في تحميل سندات الخزينة: {str(e)}', 'error')
        return redirect(url_for('treasury.detail', id=id))


@bp.route('/<id>/transfers')
def transfers(id):
    """تحويلات الخزينة"""
    try:
        safe = TreasuryService.get_safe_by_id(id)
        if not safe:
            flash('الخزينة غير موجودة', 'error')
            return redirect(url_for('treasury.index'))
        
        transfers = TreasuryService.get_safe_transfers(id)
        
        return render_template('treasury/transfers.html', safe=safe, transfers=transfers)
    except Exception as e:
        flash(f'خطأ في تحميل تحويلات الخزينة: {str(e)}', 'error')
        return redirect(url_for('treasury.detail', id=id))


@bp.route('/<id>/financial')
def financial(id):
    """الملخص المالي للخزينة"""
    try:
        safe = TreasuryService.get_safe_by_id(id)
        if not safe:
            flash('الخزينة غير موجودة', 'error')
            return redirect(url_for('treasury.index'))
        
        # إحصائيات الخزينة
        stats = TreasuryService.get_safe_statistics(id)
        
        # السندات المدفوعة
        income_vouchers = TreasuryService.get_safe_vouchers_by_type(id, 'إيراد')
        
        # السندات المصروفة
        expense_vouchers = TreasuryService.get_safe_vouchers_by_type(id, 'مصروف')
        
        return render_template('treasury/financial.html',
                             safe=safe,
                             stats=stats,
                             income_vouchers=income_vouchers,
                             expense_vouchers=expense_vouchers)
    except Exception as e:
        flash(f'خطأ في تحميل الملخص المالي: {str(e)}', 'error')
        return redirect(url_for('treasury.detail', id=id))


@bp.route('/main')
def main():
    """الخزينة الرئيسية"""
    try:
        main_safe = TreasuryService.get_main_safe()
        if not main_safe:
            flash('لا توجد خزينة رئيسية', 'error')
            return redirect(url_for('treasury.index'))
        
        return redirect(url_for('treasury.detail', id=main_safe.id))
    except Exception as e:
        flash(f'خطأ في تحميل الخزينة الرئيسية: {str(e)}', 'error')
        return redirect(url_for('treasury.index'))


@bp.route('/by-project/<project_id>')
def by_project(project_id):
    """خزائن المشروع"""
    try:
        project = ProjectService.get_project_by_id(project_id)
        if not project:
            flash('المشروع غير موجود', 'error')
            return redirect(url_for('treasury.index'))
        
        safes = TreasuryService.get_safes_by_project(project_id)
        
        return render_template('treasury/by_project.html', project=project, safes=safes)
    except Exception as e:
        flash(f'خطأ في تحميل خزائن المشروع: {str(e)}', 'error')
        return redirect(url_for('treasury.index'))


@bp.route('/project-summary/<project_id>')
def project_summary(project_id):
    """ملخص مالي للمشروع"""
    try:
        project = ProjectService.get_project_by_id(project_id)
        if not project:
            flash('المشروع غير موجود', 'error')
            return redirect(url_for('treasury.index'))
        
        summary = TreasuryService.get_project_financial_summary(project_id)
        
        return render_template('treasury/project_summary.html', project=project, summary=summary)
    except Exception as e:
        flash(f'خطأ في تحميل الملخص المالي للمشروع: {str(e)}', 'error')
        return redirect(url_for('treasury.index'))


@bp.route('/by-date-range')
def by_date_range():
    """السندات في نطاق تاريخ معين"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        safe_id = request.args.get('safe_id')
        voucher_type = request.args.get('voucher_type')
        
        if not all([start_date, end_date]):
            flash('نطاق التاريخ مطلوب', 'error')
            return redirect(url_for('treasury.index'))
        
        vouchers = TreasuryService.get_vouchers_by_date_range(start_date, end_date, safe_id, voucher_type)
        
        return render_template('treasury/by_date_range.html', vouchers=vouchers, start_date=start_date, end_date=end_date, safe_id=safe_id, voucher_type=voucher_type)
    except Exception as e:
        flash(f'خطأ في تحميل السندات حسب التاريخ: {str(e)}', 'error')
        return render_template('treasury/by_date_range.html', vouchers=[], start_date='', end_date='', safe_id='', voucher_type='')


@bp.route('/by-amount-range')
def by_amount_range():
    """السندات في نطاق مبلغ معين"""
    try:
        min_amount = request.args.get('min_amount', type=float)
        max_amount = request.args.get('max_amount', type=float)
        safe_id = request.args.get('safe_id')
        voucher_type = request.args.get('voucher_type')
        
        if not all([min_amount, max_amount]):
            flash('نطاق المبلغ مطلوب', 'error')
            return redirect(url_for('treasury.index'))
        
        vouchers = TreasuryService.get_vouchers_by_amount_range(min_amount, max_amount, safe_id, voucher_type)
        
        return render_template('treasury/by_amount_range.html', vouchers=vouchers, min_amount=min_amount, max_amount=max_amount, safe_id=safe_id, voucher_type=voucher_type)
    except Exception as e:
        flash(f'خطأ في تحميل السندات حسب المبلغ: {str(e)}', 'error')
        return render_template('treasury/by_amount_range.html', vouchers=[], min_amount=0, max_amount=0, safe_id='', voucher_type='')


@bp.route('/search-vouchers')
def search_vouchers():
    """البحث في السندات"""
    try:
        search_term = request.args.get('search', '').strip()
        
        if not search_term:
            flash('مصطلح البحث مطلوب', 'error')
            return redirect(url_for('treasury.index'))
        
        vouchers = TreasuryService.search_vouchers(search_term)
        
        return render_template('treasury/search_vouchers.html', vouchers=vouchers, search_term=search_term)
    except Exception as e:
        flash(f'خطأ في البحث في السندات: {str(e)}', 'error')
        return render_template('treasury/search_vouchers.html', vouchers=[], search_term='')


@bp.route('/update-balances', methods=['POST'])
def update_balances():
    """تحديث أرصدة جميع الخزائن"""
    try:
        updated_count = TreasuryService.update_safe_balances()
        flash(f'تم تحديث {updated_count} خزينة', 'success')
    except Exception as e:
        flash(f'خطأ في تحديث الأرصدة: {str(e)}', 'error')
    
    return redirect(url_for('treasury.index'))