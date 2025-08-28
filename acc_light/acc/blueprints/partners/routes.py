from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.partners import bp
from acc.models import Partner, PartnerGroup, PartnerGroupMember, UnitPartner, PartnerDebt
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination, parse_number
from sqlalchemy import func

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Base query
    query = Partner.query
    
    # Search
    if search:
        query = query.filter(
            db.or_(
                Partner.name.ilike(f'%{search}%'),
                Partner.phone.ilike(f'%{search}%'),
                Partner.national_id.ilike(f'%{search}%')
            )
        )
    
    # Order by name
    query = query.order_by(Partner.name)
    
    # Pagination
    pagination = Pagination(query, page)
    partners = pagination.items
    
    # Calculate stats
    total_partners = Partner.query.count()
    total_groups = PartnerGroup.query.count()
    
    # Partners with units
    partners_with_units = db.session.query(func.count(func.distinct(UnitPartner.partner_id))).scalar() or 0
    
    return render_template('partners/index.html',
                         partners=partners,
                         pagination=pagination,
                         search=search,
                         total_partners=total_partners,
                         total_groups=total_groups,
                         partners_with_units=partners_with_units)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        national_id = request.form.get('national_id', '').strip()
        address = request.form.get('address', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not name:
            flash('الرجاء إدخال اسم الشريك', 'error')
            return redirect(url_for('partners.add'))
        
        # Check duplicate national ID
        if national_id and Partner.query.filter_by(national_id=national_id).first():
            flash('الرقم القومي مسجل مسبقاً', 'error')
            return redirect(url_for('partners.add'))
        
        partner = Partner(
            id=generate_uid('PR'),
            name=name,
            phone=phone,
            national_id=national_id,
            address=address,
            notes=notes
        )
        
        db.session.add(partner)
        log_action('إضافة شريك جديد', {'id': partner.id, 'name': partner.name})
        db.session.commit()
        
        flash('تم إضافة الشريك بنجاح', 'success')
        return redirect(url_for('partners.detail', id=partner.id))
    
    return render_template('partners/add.html')


@bp.route('/<id>')
def detail(id):
    partner = Partner.query.get_or_404(id)
    
    # Get partner units
    unit_partners = UnitPartner.query.filter_by(partner_id=id).all()
    
    # Get partner groups
    group_memberships = PartnerGroupMember.query.filter_by(partner_id=id).all()
    
    # Get partner debts
    debts_owed = PartnerDebt.query.filter_by(creditor_id=id).all()
    debts_due = PartnerDebt.query.filter_by(debtor_id=id).all()
    
    # Calculate totals
    total_percentage = sum(up.percentage for up in unit_partners)
    total_owed = sum(debt.remaining_amount for debt in debts_owed)
    total_due = sum(debt.remaining_amount for debt in debts_due)
    
    return render_template('partners/detail.html',
                         partner=partner,
                         unit_partners=unit_partners,
                         group_memberships=group_memberships,
                         debts_owed=debts_owed,
                         debts_due=debts_due,
                         total_percentage=total_percentage,
                         total_owed=total_owed,
                         total_due=total_due)


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    partner = Partner.query.get_or_404(id)
    
    if request.method == 'POST':
        partner.name = request.form.get('name', '').strip()
        partner.phone = request.form.get('phone', '').strip()
        partner.national_id = request.form.get('national_id', '').strip()
        partner.address = request.form.get('address', '').strip()
        partner.notes = request.form.get('notes', '').strip()
        
        if not partner.name:
            flash('الرجاء إدخال اسم الشريك', 'error')
            return redirect(url_for('partners.edit', id=id))
        
        # Check duplicate national ID
        if partner.national_id:
            existing = Partner.query.filter_by(national_id=partner.national_id).first()
            if existing and existing.id != id:
                flash('الرقم القومي مسجل مسبقاً', 'error')
                return redirect(url_for('partners.edit', id=id))
        
        log_action('تعديل شريك', {'id': partner.id, 'name': partner.name})
        db.session.commit()
        
        flash('تم تحديث بيانات الشريك بنجاح', 'success')
        return redirect(url_for('partners.detail', id=id))
    
    return render_template('partners/edit.html', partner=partner)


# Partner Groups
@bp.route('/groups')
def groups():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Base query
    query = PartnerGroup.query
    
    # Search
    if search:
        query = query.filter(PartnerGroup.name.ilike(f'%{search}%'))
    
    # Order by name
    query = query.order_by(PartnerGroup.name)
    
    # Pagination
    pagination = Pagination(query, page)
    groups = pagination.items
    
    return render_template('partners/groups.html',
                         groups=groups,
                         pagination=pagination,
                         search=search)


@bp.route('/groups/add', methods=['GET', 'POST'])
def add_group():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not name:
            flash('الرجاء إدخال اسم المجموعة', 'error')
            return redirect(url_for('partners.add_group'))
        
        # Check duplicate
        if PartnerGroup.query.filter_by(name=name).first():
            flash('اسم المجموعة موجود بالفعل', 'error')
            return redirect(url_for('partners.add_group'))
        
        group = PartnerGroup(
            name=name,
            notes=notes
        )
        
        db.session.add(group)
        log_action('إضافة مجموعة شركاء', {'id': group.id, 'name': group.name})
        db.session.commit()
        
        flash('تم إضافة المجموعة بنجاح', 'success')
        return redirect(url_for('partners.group_detail', id=group.id))
    
    return render_template('partners/add_group.html')


@bp.route('/groups/<id>')
def group_detail(id):
    group = PartnerGroup.query.get_or_404(id)
    
    # Get units assigned to this group
    from acc.models import Unit
    units_with_group = Unit.query.join(UnitPartner).join(PartnerGroupMember).filter(
        PartnerGroupMember.group_id == id
    ).distinct().all()
    
    return render_template('partners/group_detail.html',
                         group=group,
                         units_with_group=units_with_group)


@bp.route('/groups/<id>/add-member', methods=['POST'])
def add_group_member(id):
    group = PartnerGroup.query.get_or_404(id)
    partner_id = request.form.get('partner_id')
    percentage = parse_number(request.form.get('percentage', 0))
    
    if not partner_id:
        flash('الرجاء اختيار الشريك', 'error')
        return redirect(url_for('partners.group_detail', id=id))
    
    if percentage <= 0 or percentage > 100:
        flash('الرجاء إدخال نسبة صحيحة', 'error')
        return redirect(url_for('partners.group_detail', id=id))
    
    # Check if already member
    existing = PartnerGroupMember.query.filter_by(
        group_id=id,
        partner_id=partner_id
    ).first()
    
    if existing:
        flash('هذا الشريك موجود بالفعل في المجموعة', 'error')
        return redirect(url_for('partners.group_detail', id=id))
    
    # Check total percentage
    current_total = group.get_total_percentage()
    if current_total + percentage > 100:
        flash(f'إجمالي النسب لا يمكن أن يتجاوز 100%. النسبة الحالية: {current_total}%', 'error')
        return redirect(url_for('partners.group_detail', id=id))
    
    member = PartnerGroupMember(
        group_id=id,
        partner_id=partner_id,
        percentage=percentage
    )
    
    db.session.add(member)
    log_action('إضافة شريك لمجموعة', {
        'group_id': id,
        'partner_id': partner_id,
        'percentage': percentage
    })
    db.session.commit()
    
    flash('تم إضافة الشريك للمجموعة بنجاح', 'success')
    return redirect(url_for('partners.group_detail', id=id))


@bp.route('/groups/<group_id>/remove-member/<member_id>', methods=['POST'])
def remove_group_member(group_id, member_id):
    member = PartnerGroupMember.query.get_or_404(member_id)
    
    if member.group_id != group_id:
        flash('خطأ في البيانات', 'error')
        return redirect(url_for('partners.group_detail', id=group_id))
    
    db.session.delete(member)
    log_action('حذف شريك من مجموعة', {
        'group_id': group_id,
        'partner_id': member.partner_id
    })
    db.session.commit()
    
    flash('تم حذف الشريك من المجموعة بنجاح', 'success')
    return redirect(url_for('partners.group_detail', id=group_id))


# Partner Debts
@bp.route('/debts/add', methods=['POST'])
def add_debt():
    creditor_id = request.form.get('creditor_id')
    debtor_id = request.form.get('debtor_id')
    unit_id = request.form.get('unit_id')
    amount = parse_number(request.form.get('amount', 0))
    description = request.form.get('description', '').strip()
    
    if not all([creditor_id, debtor_id, amount]):
        flash('الرجاء إدخال جميع البيانات المطلوبة', 'error')
        return redirect(request.referrer or url_for('partners.index'))
    
    if creditor_id == debtor_id:
        flash('لا يمكن أن يكون الدائن والمدين نفس الشخص', 'error')
        return redirect(request.referrer or url_for('partners.index'))
    
    if amount <= 0:
        flash('الرجاء إدخال مبلغ صحيح', 'error')
        return redirect(request.referrer or url_for('partners.index'))
    
    debt = PartnerDebt(
        creditor_id=creditor_id,
        debtor_id=debtor_id,
        unit_id=unit_id,
        amount=amount,
        remaining_amount=amount,
        description=description,
        status='نشط'
    )
    
    db.session.add(debt)
    log_action('إضافة دين بين شركاء', {
        'creditor_id': creditor_id,
        'debtor_id': debtor_id,
        'amount': amount
    })
    db.session.commit()
    
    flash('تم تسجيل الدين بنجاح', 'success')
    return redirect(request.referrer or url_for('partners.index'))


@bp.route('/debts/<id>/pay', methods=['POST'])
def pay_debt(id):
    debt = PartnerDebt.query.get_or_404(id)
    amount = parse_number(request.form.get('amount', 0))
    
    if amount <= 0 or amount > debt.remaining_amount:
        flash('الرجاء إدخال مبلغ صحيح', 'error')
        return redirect(request.referrer or url_for('partners.index'))
    
    debt.remaining_amount -= amount
    if debt.remaining_amount == 0:
        debt.status = 'مسدد'
    
    log_action('سداد دين بين شركاء', {
        'debt_id': id,
        'amount': amount,
        'remaining': debt.remaining_amount
    })
    db.session.commit()
    
    flash('تم تسجيل السداد بنجاح', 'success')
    return redirect(request.referrer or url_for('partners.index'))


# API endpoints for AJAX
@bp.route('/api/partners')
def api_partners():
    partners = Partner.query.order_by(Partner.name).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'phone': p.phone
    } for p in partners])


@bp.route('/api/groups')
def api_groups():
    groups = PartnerGroup.query.order_by(PartnerGroup.name).all()
    return jsonify([{
        'id': g.id,
        'name': g.name,
        'total_percentage': g.get_total_percentage()
    } for g in groups])