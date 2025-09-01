from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.services.unit_service import UnitService
from app.services.project_service import ProjectService
from app.services.partner_service import PartnerService
from app.services.utils import paginate_query

bp = Blueprint('units', __name__)


@bp.route('/')
def index():
    """قائمة الوحدات"""
    try:
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        project_id = request.args.get('project_id')
        unit_type = request.args.get('unit_type')
        search_term = request.args.get('search', '').strip()
        
        # الحصول على الوحدات
        if search_term:
            units = UnitService.search_units(search_term, project_id)
        elif status and project_id:
            units = UnitService.get_all_units(project_id, status)
        elif status:
            units = UnitService.get_all_units(status=status)
        elif project_id:
            units = UnitService.get_all_units(project_id=project_id)
        elif unit_type:
            units = UnitService.get_units_by_type(unit_type, project_id)
        else:
            units = UnitService.get_all_units()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(units, page, 20)
        
        return render_template('units/index.html',
                             units=pagination.items,
                             pagination=pagination,
                             current_status=status,
                             current_project_id=project_id,
                             current_unit_type=unit_type,
                             search_term=search_term)
    except Exception as e:
        flash(f'خطأ في تحميل قائمة الوحدات: {str(e)}', 'error')
        return render_template('units/index.html',
                             units=[],
                             pagination=None,
                             current_status=None,
                             current_project_id=None,
                             current_unit_type=None,
                             search_term='')


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """إنشاء وحدة جديدة"""
    if request.method == 'POST':
        try:
            # التحقق من البيانات
            project_id = request.form.get('project_id')
            name = request.form.get('name', '').strip()
            price = request.form.get('price')
            
            if not all([project_id, name, price]):
                flash('البيانات المطلوبة غير مكتملة', 'error')
                return render_template('units/create.html')
            
            # إنشاء الوحدة
            unit = UnitService.create_unit(
                project_id=project_id,
                name=name,
                code=request.form.get('code', '').strip() or None,
                unit_type=request.form.get('unit_type', '').strip() or None,
                floor=request.form.get('floor', '').strip() or None,
                area=request.form.get('area') or None,
                price=price,
                description=request.form.get('description', '').strip() or None,
                features=request.form.get('features', '').strip() or None,
                is_penthouse=request.form.get('is_penthouse') == 'on',
                is_ground_floor=request.form.get('is_ground_floor') == 'on',
                has_balcony=request.form.get('has_balcony') == 'on',
                has_garden=request.form.get('has_garden') == 'on',
                has_parking=request.form.get('has_parking') == 'on',
                has_elevator=request.form.get('has_elevator') == 'on'
            )
            
            flash('تم إنشاء الوحدة بنجاح', 'success')
            return redirect(url_for('units.detail', id=unit.id))
        except Exception as e:
            flash(f'خطأ في إنشاء الوحدة: {str(e)}', 'error')
    
    # الحصول على المشاريع للقائمة المنسدلة
    projects = ProjectService.get_active_projects()
    
    return render_template('units/create.html', projects=projects)


@bp.route('/<id>')
def detail(id):
    """تفاصيل الوحدة"""
    try:
        unit = UnitService.get_unit_by_id(id)
        if not unit:
            flash('الوحدة غير موجودة', 'error')
            return redirect(url_for('units.index'))
        
        # إحصائيات الوحدة
        stats = UnitService.get_unit_statistics(id)
        
        # العقود حسب الحالة
        contracts_by_status = {
            'نشط': UnitService.get_unit_contracts_by_status(id, 'نشط'),
            'ملغي': UnitService.get_unit_contracts_by_status(id, 'ملغي')
        }
        
        # الشركاء
        partners = UnitService.get_unit_partners(id)
        
        return render_template('units/detail.html',
                             unit=unit,
                             stats=stats,
                             contracts_by_status=contracts_by_status,
                             partners=partners)
    except Exception as e:
        flash(f'خطأ في تحميل تفاصيل الوحدة: {str(e)}', 'error')
        return redirect(url_for('units.index'))


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    """تعديل الوحدة"""
    try:
        unit = UnitService.get_unit_by_id(id)
        if not unit:
            flash('الوحدة غير موجودة', 'error')
            return redirect(url_for('units.index'))
        
        if request.method == 'POST':
            # تحديث الوحدة
            updated_unit = UnitService.update_unit(id,
                name=request.form.get('name', '').strip(),
                code=request.form.get('code', '').strip() or None,
                unit_type=request.form.get('unit_type', '').strip() or None,
                floor=request.form.get('floor', '').strip() or None,
                area=request.form.get('area') or None,
                price=request.form.get('price'),
                description=request.form.get('description', '').strip() or None,
                features=request.form.get('features', '').strip() or None,
                is_penthouse=request.form.get('is_penthouse') == 'on',
                is_ground_floor=request.form.get('is_ground_floor') == 'on',
                has_balcony=request.form.get('has_balcony') == 'on',
                has_garden=request.form.get('has_garden') == 'on',
                has_parking=request.form.get('has_parking') == 'on',
                has_elevator=request.form.get('has_elevator') == 'on',
                status=request.form.get('status', 'متاح')
            )
            
            flash('تم تحديث الوحدة بنجاح', 'success')
            return redirect(url_for('units.detail', id=id))
        
        # الحصول على المشاريع للقائمة المنسدلة
        projects = ProjectService.get_active_projects()
        
        return render_template('units/edit.html', unit=unit, projects=projects)
    except Exception as e:
        flash(f'خطأ في تحديث الوحدة: {str(e)}', 'error')
        return redirect(url_for('units.detail', id=id))


@bp.route('/<id>/delete', methods=['POST'])
def delete(id):
    """حذف الوحدة"""
    try:
        success = UnitService.delete_unit(id)
        if success:
            flash('تم حذف الوحدة بنجاح', 'success')
        else:
            flash('فشل في حذف الوحدة', 'error')
    except Exception as e:
        flash(f'خطأ في حذف الوحدة: {str(e)}', 'error')
    
    return redirect(url_for('units.index'))


@bp.route('/<id>/reserve', methods=['POST'])
def reserve(id):
    """حجز الوحدة"""
    try:
        customer_id = request.form.get('customer_id')
        notes = request.form.get('notes', '').strip()
        
        unit = UnitService.reserve_unit(id, customer_id, notes)
        flash('تم حجز الوحدة بنجاح', 'success')
        return redirect(url_for('units.detail', id=id))
    except Exception as e:
        flash(f'خطأ في حجز الوحدة: {str(e)}', 'error')
        return redirect(url_for('units.detail', id=id))


@bp.route('/<id>/release', methods=['POST'])
def release(id):
    """إلغاء حجز الوحدة"""
    try:
        unit = UnitService.release_unit(id)
        flash('تم إلغاء حجز الوحدة بنجاح', 'success')
        return redirect(url_for('units.detail', id=id))
    except Exception as e:
        flash(f'خطأ في إلغاء حجز الوحدة: {str(e)}', 'error')
        return redirect(url_for('units.detail', id=id))


@bp.route('/<id>/sell', methods=['POST'])
def sell(id):
    """بيع الوحدة"""
    try:
        unit = UnitService.sell_unit(id)
        flash('تم بيع الوحدة بنجاح', 'success')
        return redirect(url_for('units.detail', id=id))
    except Exception as e:
        flash(f'خطأ في بيع الوحدة: {str(e)}', 'error')
        return redirect(url_for('units.detail', id=id))


@bp.route('/<id>/contracts')
def contracts(id):
    """عقود الوحدة"""
    try:
        unit = UnitService.get_unit_by_id(id)
        if not unit:
            flash('الوحدة غير موجودة', 'error')
            return redirect(url_for('units.index'))
        
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status')
        
        # الحصول على العقود
        if status:
            contracts = UnitService.get_unit_contracts_by_status(id, status)
        else:
            contracts = unit.contracts.all()
        
        # تقسيم النتائج إلى صفحات
        pagination = paginate_query(contracts, page, 20)
        
        return render_template('units/contracts.html',
                             unit=unit,
                             contracts=pagination.items,
                             pagination=pagination,
                             current_status=status)
    except Exception as e:
        flash(f'خطأ في تحميل عقود الوحدة: {str(e)}', 'error')
        return redirect(url_for('units.detail', id=id))


@bp.route('/<id>/partners')
def partners(id):
    """شركاء الوحدة"""
    try:
        unit = UnitService.get_unit_by_id(id)
        if not unit:
            flash('الوحدة غير موجودة', 'error')
            return redirect(url_for('units.index'))
        
        partners = UnitService.get_unit_partners(id)
        
        return render_template('units/partners.html', unit=unit, partners=partners)
    except Exception as e:
        flash(f'خطأ في تحميل شركاء الوحدة: {str(e)}', 'error')
        return redirect(url_for('units.detail', id=id))


@bp.route('/<id>/add-partner', methods=['GET', 'POST'])
def add_partner(id):
    """إضافة شريك للوحدة"""
    try:
        unit = UnitService.get_unit_by_id(id)
        if not unit:
            flash('الوحدة غير موجودة', 'error')
            return redirect(url_for('units.index'))
        
        if request.method == 'POST':
            partner_id = request.form.get('partner_id')
            percentage = request.form.get('percentage', type=float)
            
            if not all([partner_id, percentage]):
                flash('البيانات المطلوبة غير مكتملة', 'error')
                return render_template('units/add_partner.html', unit=unit)
            
            # إضافة الشريك
            unit_partner = UnitService.add_partner_to_unit(id, partner_id, percentage)
            flash('تم إضافة الشريك بنجاح', 'success')
            return redirect(url_for('units.partners', id=id))
        
        # الحصول على الشركاء للقائمة المنسدلة
        partners = PartnerService.get_active_partners()
        
        return render_template('units/add_partner.html', unit=unit, partners=partners)
    except Exception as e:
        flash(f'خطأ في إضافة الشريك: {str(e)}', 'error')
        return redirect(url_for('units.partners', id=id))


@bp.route('/<id>/remove-partner/<partner_id>', methods=['POST'])
def remove_partner(id, partner_id):
    """إزالة شريك من الوحدة"""
    try:
        success = UnitService.remove_partner_from_unit(id, partner_id)
        if success:
            flash('تم إزالة الشريك بنجاح', 'success')
        else:
            flash('فشل في إزالة الشريك', 'error')
    except Exception as e:
        flash(f'خطأ في إزالة الشريك: {str(e)}', 'error')
    
    return redirect(url_for('units.partners', id=id))


@bp.route('/available')
def available():
    """الوحدات المتاحة"""
    try:
        project_id = request.args.get('project_id')
        units = UnitService.get_available_units(project_id)
        
        return render_template('units/available.html', units=units)
    except Exception as e:
        flash(f'خطأ في تحميل الوحدات المتاحة: {str(e)}', 'error')
        return render_template('units/available.html', units=[])


@bp.route('/sold')
def sold():
    """الوحدات المباعة"""
    try:
        project_id = request.args.get('project_id')
        units = UnitService.get_sold_units(project_id)
        
        return render_template('units/sold.html', units=units)
    except Exception as e:
        flash(f'خطأ في تحميل الوحدات المباعة: {str(e)}', 'error')
        return render_template('units/sold.html', units=[])


@bp.route('/reserved')
def reserved():
    """الوحدات المحجوزة"""
    try:
        project_id = request.args.get('project_id')
        units = UnitService.get_reserved_units(project_id)
        
        return render_template('units/reserved.html', units=units)
    except Exception as e:
        flash(f'خطأ في تحميل الوحدات المحجوزة: {str(e)}', 'error')
        return render_template('units/reserved.html', units=[])


@bp.route('/by-type')
def by_type():
    """الوحدات حسب النوع"""
    try:
        unit_type = request.args.get('unit_type')
        project_id = request.args.get('project_id')
        
        if not unit_type:
            flash('نوع الوحدة مطلوب', 'error')
            return redirect(url_for('units.index'))
        
        units = UnitService.get_units_by_type(unit_type, project_id)
        
        return render_template('units/by_type.html', units=units, unit_type=unit_type)
    except Exception as e:
        flash(f'خطأ في تحميل الوحدات حسب النوع: {str(e)}', 'error')
        return render_template('units/by_type.html', units=[], unit_type='')


@bp.route('/by-floor')
def by_floor():
    """الوحدات حسب الطابق"""
    try:
        floor = request.args.get('floor')
        project_id = request.args.get('project_id')
        
        if not floor:
            flash('الطابق مطلوب', 'error')
            return redirect(url_for('units.index'))
        
        units = UnitService.get_units_by_floor(floor, project_id)
        
        return render_template('units/by_floor.html', units=units, floor=floor)
    except Exception as e:
        flash(f'خطأ في تحميل الوحدات حسب الطابق: {str(e)}', 'error')
        return render_template('units/by_floor.html', units=[], floor='')


@bp.route('/by-price-range')
def by_price_range():
    """الوحدات حسب نطاق السعر"""
    try:
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        project_id = request.args.get('project_id')
        
        if not all([min_price, max_price]):
            flash('نطاق السعر مطلوب', 'error')
            return redirect(url_for('units.index'))
        
        units = UnitService.get_units_by_price_range(min_price, max_price, project_id)
        
        return render_template('units/by_price_range.html', units=units, min_price=min_price, max_price=max_price)
    except Exception as e:
        flash(f'خطأ في تحميل الوحدات حسب نطاق السعر: {str(e)}', 'error')
        return render_template('units/by_price_range.html', units=[], min_price=0, max_price=0)


@bp.route('/by-area-range')
def by_area_range():
    """الوحدات حسب نطاق المساحة"""
    try:
        min_area = request.args.get('min_area', type=float)
        max_area = request.args.get('max_area', type=float)
        project_id = request.args.get('project_id')
        
        if not all([min_area, max_area]):
            flash('نطاق المساحة مطلوب', 'error')
            return redirect(url_for('units.index'))
        
        units = UnitService.get_units_by_area_range(min_area, max_area, project_id)
        
        return render_template('units/by_area_range.html', units=units, min_area=min_area, max_area=max_area)
    except Exception as e:
        flash(f'خطأ في تحميل الوحدات حسب نطاق المساحة: {str(e)}', 'error')
        return render_template('units/by_area_range.html', units=[], min_area=0, max_area=0)


@bp.route('/with-features')
def with_features():
    """الوحدات التي تحتوي على مميزات معينة"""
    try:
        features = request.args.getlist('features')
        project_id = request.args.get('project_id')
        
        if not features:
            flash('المميزات مطلوبة', 'error')
            return redirect(url_for('units.index'))
        
        units = UnitService.get_units_with_features(features, project_id)
        
        return render_template('units/with_features.html', units=units, features=features)
    except Exception as e:
        flash(f'خطأ في تحميل الوحدات حسب المميزات: {str(e)}', 'error')
        return render_template('units/with_features.html', units=[], features=[])


@bp.route('/project-summary/<project_id>')
def project_summary(project_id):
    """ملخص وحدات المشروع"""
    try:
        project = ProjectService.get_project_by_id(project_id)
        if not project:
            flash('المشروع غير موجود', 'error')
            return redirect(url_for('units.index'))
        
        summary = UnitService.get_project_units_summary(project_id)
        
        return render_template('units/project_summary.html', project=project, summary=summary)
    except Exception as e:
        flash(f'خطأ في تحميل ملخص وحدات المشروع: {str(e)}', 'error')
        return redirect(url_for('units.index'))