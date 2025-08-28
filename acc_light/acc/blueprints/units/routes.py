from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.units import bp
from acc.extensions import db
from acc.models import Unit, Partner, PartnerGroup, PartnerGroupMember, UnitPartner, Contract
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from acc.services.project_context import get_current_project, filter_by_project
from sqlalchemy import or_


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    
    # Start with filtered query by project
    query = filter_by_project(Unit.query, Unit)
    
    if q:
        query = query.filter(
            or_(
                Unit.code.contains(q),
                Unit.name.contains(q),
                Unit.floor.contains(q),
                Unit.building.contains(q)
            )
        )
    
    if status_filter:
        query = query.filter(Unit.status == status_filter)
    
    query = query.order_by(Unit.code)
    pagination = Pagination(query, page)
    
    # Get partner names for each unit
    units_data = []
    for unit in pagination.items:
        partners = []
        for up in unit.partners:
            partner = Partner.query.get(up.partner_id)
            if partner:
                partners.append(f"{partner.name} ({up.percentage}%)")
        units_data.append({
            'unit': unit,
            'partners': ', '.join(partners) if partners else 'لا يوجد شركاء',
            'remaining': unit.calculate_remaining()
        })
    
    return render_template('units/index.html',
                         units_data=units_data,
                         pagination=pagination,
                         q=q,
                         status_filter=status_filter,
                         format_currency=format_currency)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        floor = request.form.get('floor', '').strip()
        building = request.form.get('building', '').strip()
        area = request.form.get('area', '').strip()
        unit_type = request.form.get('unit_type', 'سكني')
        total_price = float(request.form.get('total_price', 0) or 0)
        partner_group_id = request.form.get('partner_group_id')
        notes = request.form.get('notes', '').strip()
        
        if not all([name, floor, building]):
            flash('الرجاء إدخال اسم الوحدة والدور والمبنى.', 'error')
            return redirect(url_for('units.add'))
        
        if total_price <= 0:
            flash('الرجاء إدخال سعر صحيح للوحدة.', 'error')
            return redirect(url_for('units.add'))
        
        # Generate unit code
        code = f"{building}-{floor}-{name}"
        
        # Check if unit exists
        if Unit.query.filter_by(code=code).first():
            flash('وحدة بنفس الكود موجودة بالفعل.', 'error')
            return redirect(url_for('units.add'))
        
        # Get current project
        current_project = get_current_project()
        if not current_project:
            flash('الرجاء اختيار مشروع أولاً', 'error')
            return redirect(url_for('projects.index'))
        
        # Create unit
        unit = Unit(
            id=generate_uid('U'),
            project_id=current_project.id,
            code=code,
            name=name,
            floor=floor,
            building=building,
            area=float(area) if area else None,
            unit_type=unit_type,
            total_price=total_price,
            status='متاحة',
            notes=notes
        )
        
        db.session.add(unit)
        
        # Add partners from group if selected
        if partner_group_id:
            group = PartnerGroup.query.get(partner_group_id)
            if group:
                for member in group.members:
                    unit_partner = UnitPartner(
                        unit_id=unit.id,
                        partner_id=member.partner_id,
                        percentage=member.percentage
                    )
                    db.session.add(unit_partner)
        
        log_action('إضافة وحدة جديدة', {'id': unit.id, 'code': unit.code})
        db.session.commit()
        
        flash('تم إضافة الوحدة بنجاح.', 'success')
        return redirect(url_for('units.detail', id=unit.id))
    
    partner_groups = PartnerGroup.query.all()
    return render_template('units/add.html', partner_groups=partner_groups)


@bp.route('/<string:id>')
def detail(id):
    unit = Unit.query.get_or_404(id)
    
    # Get partners with details
    partners_data = []
    total_percentage = 0
    for up in unit.partners:
        partner = Partner.query.get(up.partner_id)
        if partner:
            partners_data.append({
                'link': up,
                'partner': partner,
                'percentage': up.percentage
            })
            total_percentage += up.percentage
    
    # Get available partners to add
    existing_partner_ids = [up.partner_id for up in unit.partners]
    available_partners = Partner.query.filter(~Partner.id.in_(existing_partner_ids)).all() if existing_partner_ids else Partner.query.all()
    
    # Check if unit has contract
    has_contract = Contract.query.filter_by(unit_id=id).first() is not None
    
    return render_template('units/detail.html',
                         unit=unit,
                         partners_data=partners_data,
                         total_percentage=total_percentage,
                         available_partners=available_partners,
                         has_contract=has_contract,
                         format_currency=format_currency)


@bp.route('/<string:id>/edit', methods=['GET', 'POST'])
def edit(id):
    unit = Unit.query.get_or_404(id)
    
    # Check if unit has contract
    if unit.status == 'مباعة':
        flash('لا يمكن تعديل وحدة مباعة.', 'error')
        return redirect(url_for('units.detail', id=id))
    
    if request.method == 'POST':
        unit.name = request.form.get('name', '').strip()
        unit.floor = request.form.get('floor', '').strip()
        unit.building = request.form.get('building', '').strip()
        unit.area = float(request.form.get('area') or 0) if request.form.get('area') else None
        unit.unit_type = request.form.get('unit_type', 'سكني')
        unit.total_price = float(request.form.get('total_price', 0) or 0)
        unit.notes = request.form.get('notes', '').strip()
        
        if not all([unit.name, unit.floor, unit.building]):
            flash('الرجاء إدخال اسم الوحدة والدور والمبنى.', 'error')
            return redirect(url_for('units.edit', id=id))
        
        # Update code
        unit.code = f"{unit.building}-{unit.floor}-{unit.name}"
        
        log_action('تعديل بيانات وحدة', {'id': unit.id, 'code': unit.code})
        db.session.commit()
        
        flash('تم تحديث بيانات الوحدة بنجاح.', 'success')
        return redirect(url_for('units.detail', id=id))
    
    return render_template('units/edit.html', unit=unit)


@bp.route('/<string:id>/delete', methods=['POST'])
def delete(id):
    unit = Unit.query.get_or_404(id)
    
    # Check if unit has contracts
    if Contract.query.filter_by(unit_id=id).count() > 0:
        flash('لا يمكن حذف هذه الوحدة لأنها مرتبطة بعقود.', 'error')
        return redirect(url_for('units.index'))
    
    log_action('حذف وحدة', {'id': unit.id, 'code': unit.code})
    db.session.delete(unit)
    db.session.commit()
    
    flash('تم حذف الوحدة بنجاح.', 'success')
    return redirect(url_for('units.index'))


@bp.route('/<string:id>/add-partner', methods=['POST'])
def add_partner(id):
    unit = Unit.query.get_or_404(id)
    
    partner_id = request.form.get('partner_id')
    percentage = float(request.form.get('percentage', 0) or 0)
    
    if not partner_id or percentage <= 0:
        flash('الرجاء اختيار شريك وإدخال نسبة صحيحة.', 'error')
        return redirect(url_for('units.detail', id=id))
    
    # Check total percentage
    current_total = sum(up.percentage for up in unit.partners)
    if current_total + percentage > 100:
        flash(f'لا يمكن إضافة هذه النسبة. المجموع الحالي {current_total}% والمجموع سيصبح {current_total + percentage}%.', 'error')
        return redirect(url_for('units.detail', id=id))
    
    # Add partner
    unit_partner = UnitPartner(
        unit_id=id,
        partner_id=partner_id,
        percentage=percentage
    )
    
    db.session.add(unit_partner)
    log_action('إضافة شريك لوحدة', {'unit_id': id, 'partner_id': partner_id, 'percentage': percentage})
    db.session.commit()
    
    flash('تم إضافة الشريك بنجاح.', 'success')
    return redirect(url_for('units.detail', id=id))


@bp.route('/partner/<string:link_id>/remove', methods=['POST'])
def remove_partner(link_id):
    link = UnitPartner.query.get_or_404(link_id)
    unit_id = link.unit_id
    
    log_action('حذف شريك من وحدة', {'link_id': link_id, 'unit_id': unit_id})
    db.session.delete(link)
    db.session.commit()
    
    flash('تم حذف الشريك من الوحدة.', 'success')
    return redirect(url_for('units.detail', id=unit_id))


@bp.route('/partner/<string:link_id>/update', methods=['POST'])
def update_partner_percentage(link_id):
    link = UnitPartner.query.get_or_404(link_id)
    new_percentage = float(request.form.get('percentage', 0) or 0)
    
    if new_percentage <= 0 or new_percentage > 100:
        return jsonify({'success': False, 'message': 'النسبة يجب أن تكون بين 1 و 100'})
    
    # Check total
    unit = Unit.query.get(link.unit_id)
    current_total = sum(up.percentage for up in unit.partners if up.id != link_id)
    if current_total + new_percentage > 100:
        return jsonify({'success': False, 'message': f'المجموع سيتجاوز 100% ({current_total + new_percentage}%)'})
    
    link.percentage = new_percentage
    log_action('تحديث نسبة شريك', {'link_id': link_id, 'new_percentage': new_percentage})
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم تحديث النسبة بنجاح'})


@bp.route('/search')
def search():
    """HTMX endpoint for live search"""
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Unit.query
    
    if q:
        query = query.filter(
            or_(
                Unit.code.contains(q),
                Unit.name.contains(q),
                Unit.floor.contains(q),
                Unit.building.contains(q)
            )
        )
    
    if status_filter:
        query = query.filter(Unit.status == status_filter)
    
    query = query.order_by(Unit.code)
    pagination = Pagination(query, page)
    
    # Get partner names for each unit
    units_data = []
    for unit in pagination.items:
        partners = []
        for up in unit.partners:
            partner = Partner.query.get(up.partner_id)
            if partner:
                partners.append(f"{partner.name} ({up.percentage}%)")
        units_data.append({
            'unit': unit,
            'partners': ', '.join(partners) if partners else 'لا يوجد شركاء',
            'remaining': unit.calculate_remaining()
        })
    
    return render_template('units/_table.html',
                         units_data=units_data,
                         pagination=pagination,
                         format_currency=format_currency)