from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.services.project_service import ProjectService
from app.services.contractor_service import ContractorService
from app.services.utils import paginate_query

bp = Blueprint('projects', __name__)


@bp.route('/')
def index():
    """قائمة المشاريع"""
    try:
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        search_term = request.args.get('search', '').strip()
        
        # الحصول على المشاريع
        if search_term:
            projects = ProjectService.search_projects(search_term)
        elif status:
            projects = ProjectService.get_all_projects(status)
        else:
            projects = ProjectService.get_all_projects()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(projects, page, 20)
        
        return render_template('projects/index.html',
                             projects=pagination.items,
                             pagination=pagination,
                             current_status=status,
                             search_term=search_term)
    except Exception as e:
        flash(f'خطأ في تحميل قائمة المشاريع: {str(e)}', 'error')
        return render_template('projects/index.html',
                             projects=[],
                             pagination=None,
                             current_status=None,
                             search_term='')


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """إنشاء مشروع جديد"""
    if request.method == 'POST':
        try:
            # التحقق من البيانات
            name = request.form.get('name', '').strip()
            if not name:
                flash('اسم المشروع مطلوب', 'error')
                return render_template('projects/create.html')
            
            # إنشاء المشروع
            project = ProjectService.create_project(
                name=name,
                code=request.form.get('code', '').strip() or None,
                description=request.form.get('description', '').strip() or None,
                project_type=request.form.get('project_type', 'عقاري'),
                location=request.form.get('location', '').strip() or None,
                area=request.form.get('area', '').strip() or None,
                contractor_id=request.form.get('contractor_id') or None,
                start_date=request.form.get('start_date') or None,
                expected_end_date=request.form.get('expected_end_date') or None,
                budget=request.form.get('budget') or None
            )
            
            flash('تم إنشاء المشروع بنجاح', 'success')
            return redirect(url_for('projects.detail', id=project.id))
        except Exception as e:
            flash(f'خطأ في إنشاء المشروع: {str(e)}', 'error')
    
    # الحصول على المقاولين للقائمة المنسدلة
    contractors = ContractorService.get_all_contractors()
    
    return render_template('projects/create.html', contractors=contractors)


@bp.route('/<id>')
def detail(id):
    """تفاصيل المشروع"""
    try:
        project = ProjectService.get_project_by_id(id)
        if not project:
            flash('المشروع غير موجود', 'error')
            return redirect(url_for('projects.index'))
        
        # إحصائيات المشروع
        stats = ProjectService.get_project_statistics(id)
        
        # الملخص المالي
        financial_summary = ProjectService.get_project_financial_summary(id)
        
        # الوحدات حسب الحالة
        units_by_status = {
            'متاح': ProjectService.get_project_units_by_status(id, 'متاح'),
            'مباع': ProjectService.get_project_units_by_status(id, 'مباع'),
            'محجوز': ProjectService.get_project_units_by_status(id, 'محجوز')
        }
        
        # العقود حسب الحالة
        contracts_by_status = {
            'نشط': ProjectService.get_project_contracts_by_status(id, 'نشط'),
            'ملغي': ProjectService.get_project_contracts_by_status(id, 'ملغي')
        }
        
        return render_template('projects/detail.html',
                             project=project,
                             stats=stats,
                             financial_summary=financial_summary,
                             units_by_status=units_by_status,
                             contracts_by_status=contracts_by_status)
    except Exception as e:
        flash(f'خطأ في تحميل تفاصيل المشروع: {str(e)}', 'error')
        return redirect(url_for('projects.index'))


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    """تعديل المشروع"""
    try:
        project = ProjectService.get_project_by_id(id)
        if not project:
            flash('المشروع غير موجود', 'error')
            return redirect(url_for('projects.index'))
        
        if request.method == 'POST':
            # تحديث المشروع
            updated_project = ProjectService.update_project(id,
                name=request.form.get('name', '').strip(),
                code=request.form.get('code', '').strip() or None,
                description=request.form.get('description', '').strip() or None,
                project_type=request.form.get('project_type', 'عقاري'),
                location=request.form.get('location', '').strip() or None,
                area=request.form.get('area', '').strip() or None,
                contractor_id=request.form.get('contractor_id') or None,
                start_date=request.form.get('start_date') or None,
                expected_end_date=request.form.get('expected_end_date') or None,
                budget=request.form.get('budget') or None,
                status=request.form.get('status', 'نشط')
            )
            
            flash('تم تحديث المشروع بنجاح', 'success')
            return redirect(url_for('projects.detail', id=id))
        
        # الحصول على المقاولين للقائمة المنسدلة
        contractors = ContractorService.get_all_contractors()
        
        return render_template('projects/edit.html', project=project, contractors=contractors)
    except Exception as e:
        flash(f'خطأ في تحديث المشروع: {str(e)}', 'error')
        return redirect(url_for('projects.detail', id=id))


@bp.route('/<id>/delete', methods=['POST'])
def delete(id):
    """حذف المشروع"""
    try:
        success = ProjectService.delete_project(id)
        if success:
            flash('تم حذف المشروع بنجاح', 'success')
        else:
            flash('فشل في حذف المشروع', 'error')
    except Exception as e:
        flash(f'خطأ في حذف المشروع: {str(e)}', 'error')
    
    return redirect(url_for('projects.index'))


@bp.route('/<id>/set-default', methods=['POST'])
def set_default(id):
    """تعيين المشروع كافتراضي"""
    try:
        success = ProjectService.set_default_project(id)
        if success:
            flash('تم تعيين المشروع كافتراضي بنجاح', 'success')
        else:
            flash('فشل في تعيين المشروع كافتراضي', 'error')
    except Exception as e:
        flash(f'خطأ في تعيين المشروع كافتراضي: {str(e)}', 'error')
    
    return redirect(url_for('projects.detail', id=id))


@bp.route('/<id>/units')
def units(id):
    """وحدات المشروع"""
    try:
        project = ProjectService.get_project_by_id(id)
        if not project:
            flash('المشروع غير موجود', 'error')
            return redirect(url_for('projects.index'))
        
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        
        # الحصول على الوحدات
        if status:
            units = ProjectService.get_project_units_by_status(id, status)
        else:
            units = project.units.all()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(units, page, 20)
        
        return render_template('projects/units.html',
                             project=project,
                             units=pagination.items,
                             pagination=pagination,
                             current_status=status)
    except Exception as e:
        flash(f'خطأ في تحميل وحدات المشروع: {str(e)}', 'error')
        return redirect(url_for('projects.detail', id=id))


@bp.route('/<id>/contracts')
def contracts(id):
    """عقود المشروع"""
    try:
        project = ProjectService.get_project_by_id(id)
        if not project:
            flash('المشروع غير موجود', 'error')
            return redirect(url_for('projects.index'))
        
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        
        # الحصول على العقود
        if status:
            contracts = ProjectService.get_project_contracts_by_status(id, status)
        else:
            contracts = project.contracts.all()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(contracts, page, 20)
        
        return render_template('projects/contracts.html',
                             project=project,
                             contracts=pagination.items,
                             pagination=pagination,
                             current_status=status)
    except Exception as e:
        flash(f'خطأ في تحميل عقود المشروع: {str(e)}', 'error')
        return redirect(url_for('projects.detail', id=id))


@bp.route('/<id>/financial')
def financial(id):
    """الملخص المالي للمشروع"""
    try:
        project = ProjectService.get_project_by_id(id)
        if not project:
            flash('المشروع غير موجود', 'error')
            return redirect(url_for('projects.index'))
        
        # الملخص المالي
        financial_summary = ProjectService.get_project_financial_summary(id)
        
        return render_template('projects/financial.html',
                             project=project,
                             financial_summary=financial_summary)
    except Exception as e:
        flash(f'خطأ في تحميل الملخص المالي: {str(e)}', 'error')
        return redirect(url_for('projects.detail', id=id))