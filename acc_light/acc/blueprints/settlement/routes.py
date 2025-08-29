from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.settlement import bp
from acc.models import (Phase, Project, ProjectPartner, Partner, Expense, MaterialIssue,
                       Material, PhaseSettlementLine)
from acc.extensions import db
from acc.services.settlement_service import (compute_phase_settlement, settle_phase, 
                                           get_project_ledger, get_phase_expenses_details)
from acc.services.utils import generate_uid, log_action, get_today
from acc.services.project_context import filter_by_project, get_current_project
from datetime import datetime


@bp.route('/phases')
def phases_index():
    """قائمة المراحل"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    project_id = request.args.get('project_id', '')
    status = request.args.get('status', '')
    
    query = Phase.query
    
    # فلترة حسب المشروع
    if project_id:
        query = query.filter_by(project_id=project_id)
    else:
        # فلترة حسب المشروع الحالي
        current_project = get_current_project()
        if current_project:
            query = query.filter_by(project_id=current_project.id)
    
    # البحث
    if search:
        query = query.filter(
            db.or_(
                Phase.name.ilike(f'%{search}%'),
                Phase.description.ilike(f'%{search}%')
            )
        )
    
    # فلترة حسب الحالة
    if status == 'settled':
        query = query.filter(Phase.settled_at.isnot(None))
    elif status == 'pending':
        query = query.filter(Phase.settled_at.is_(None))
    
    # ترتيب
    query = query.order_by(Phase.created_at.desc())
    
    # صفحات
    phases = query.paginate(page=page, per_page=20, error_out=False)
    
    # جلب المشاريع
    projects = Project.query.filter_by(status='نشط').order_by(Project.name).all()
    
    return render_template('settlement/phases_index.html',
                         phases=phases,
                         projects=projects,
                         search=search,
                         project_id=project_id,
                         status=status)


@bp.route('/phases/add', methods=['GET', 'POST'])
def add_phase():
    """إضافة مرحلة جديدة"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        project_id = request.form.get('project_id')
        description = request.form.get('description', '').strip()
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if not name:
            flash('الرجاء إدخال اسم المرحلة', 'error')
            return redirect(url_for('settlement.add_phase'))
        
        if not project_id:
            flash('الرجاء اختيار المشروع', 'error')
            return redirect(url_for('settlement.add_phase'))
        
        phase = Phase(
            id=generate_uid('PH'),
            name=name,
            project_id=project_id,
            description=description,
            start_date=datetime.strptime(start_date, '%Y-%m-%d') if start_date else None,
            end_date=datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
        )
        
        db.session.add(phase)
        log_action('إضافة مرحلة جديدة', {'id': phase.id, 'name': phase.name})
        db.session.commit()
        
        flash('تم إضافة المرحلة بنجاح', 'success')
        return redirect(url_for('settlement.phase_detail', id=phase.id))
    
    projects = Project.query.filter_by(status='نشط').order_by(Project.name).all()
    current_project = get_current_project()
    
    return render_template('settlement/add_phase.html',
                         projects=projects,
                         current_project=current_project,
                         today=get_today())


@bp.route('/phases/<id>')
def phase_detail(id):
    """تفاصيل المرحلة"""
    phase = Phase.query.get_or_404(id)
    
    # جلب تفاصيل المصروفات
    details = get_phase_expenses_details(id)
    
    # جلب الشركاء في المشروع
    project_partners = ProjectPartner.query.filter_by(
        project_id=phase.project_id,
        is_active=True
    ).all()
    
    # إذا كانت المرحلة غير متسوية، احسب معاينة التسوية
    settlement_preview = None
    if not phase.is_settled:
        settlement_preview = compute_phase_settlement(id)
    
    # جلب سجل التسوية إذا كانت متسوية
    settlement_record = None
    if phase.is_settled:
        settlement_record = phase.settlements.first()
    
    # جلب المواد للقائمة المنسدلة
    materials = Material.query.order_by(Material.name).all()
    
    return render_template('settlement/phase_detail.html',
                         phase=phase,
                         details=details,
                         project_partners=project_partners,
                         settlement_preview=settlement_preview,
                         settlement_record=settlement_record,
                         materials=materials,
                         Partner=Partner,
                         get_today=get_today)


@bp.route('/phases/<id>/add-expense', methods=['POST'])
def add_expense(id):
    """إضافة مصروف للمرحلة"""
    phase = Phase.query.get_or_404(id)
    
    if phase.is_settled:
        flash('لا يمكن إضافة مصروفات لمرحلة متسوية', 'error')
        return redirect(url_for('settlement.phase_detail', id=id))
    
    partner_id = request.form.get('partner_id')
    amount = float(request.form.get('amount', 0))
    category = request.form.get('category', '').strip()
    description = request.form.get('description', '').strip()
    expense_date = request.form.get('expense_date')
    receipt_number = request.form.get('receipt_number', '').strip()
    
    if not partner_id or amount <= 0:
        flash('الرجاء إدخال بيانات صحيحة', 'error')
        return redirect(url_for('settlement.phase_detail', id=id))
    
    expense = Expense(
        id=generate_uid('EXP'),
        phase_id=id,
        paid_by_partner_id=partner_id,
        amount=amount,
        category=category,
        description=description,
        expense_date=datetime.strptime(expense_date, '%Y-%m-%d') if expense_date else datetime.now(),
        receipt_number=receipt_number
    )
    
    db.session.add(expense)
    log_action('إضافة مصروف', {'phase_id': id, 'amount': amount})
    db.session.commit()
    
    flash('تم إضافة المصروف بنجاح', 'success')
    return redirect(url_for('settlement.phase_detail', id=id))


@bp.route('/phases/<id>/add-material', methods=['POST'])
def add_material_issue(id):
    """إضافة صرف مواد للمرحلة"""
    phase = Phase.query.get_or_404(id)
    
    if phase.is_settled:
        flash('لا يمكن إضافة مواد لمرحلة متسوية', 'error')
        return redirect(url_for('settlement.phase_detail', id=id))
    
    material_id = request.form.get('material_id')
    quantity = float(request.form.get('quantity', 0))
    unit_cost = float(request.form.get('unit_cost', 0))
    partner_id = request.form.get('partner_id')
    notes = request.form.get('notes', '').strip()
    issue_date = request.form.get('issue_date')
    
    if not material_id or quantity <= 0 or unit_cost <= 0:
        flash('الرجاء إدخال بيانات صحيحة', 'error')
        return redirect(url_for('settlement.phase_detail', id=id))
    
    issue = MaterialIssue(
        id=generate_uid('MISS'),
        phase_id=id,
        material_id=material_id,
        quantity=quantity,
        unit_cost=unit_cost,
        issued_by_partner_id=partner_id if partner_id else None,
        notes=notes,
        issue_date=datetime.strptime(issue_date, '%Y-%m-%d') if issue_date else datetime.now()
    )
    
    db.session.add(issue)
    log_action('صرف مواد', {'phase_id': id, 'material_id': material_id, 'quantity': quantity})
    db.session.commit()
    
    flash('تم إضافة صرف المواد بنجاح', 'success')
    return redirect(url_for('settlement.phase_detail', id=id))


@bp.route('/phase/<id>/preview', methods=['GET'])
def preview_settlement(id):
    """معاينة تسوية المرحلة (JSON)"""
    calculation = compute_phase_settlement(id)
    
    if calculation.get('error'):
        return jsonify({'error': calculation['error']}), 400
    
    # تحويل البيانات لـ JSON
    result = {
        'phase_name': calculation['phase'].name,
        'total_expenses': calculation['total_expenses'],
        'total_materials': calculation['total_materials'],
        'total_cost': calculation['total_cost'],
        'partners_count': calculation['partners_count'],
        'average_per_partner': calculation['average_per_partner'],
        'can_settle': calculation['can_settle'],
        'partners': []
    }
    
    for partner_data in calculation['partners_data']:
        result['partners'].append({
            'id': partner_data['partner'].id,
            'name': partner_data['partner'].name,
            'paid_amount': partner_data['paid_amount'],
            'difference': partner_data['difference'],
            'current_balance': partner_data['current_balance'],
            'new_balance': partner_data['new_balance'],
            'status': 'عليه دفع' if partner_data['difference'] > 0 else ('له استرداد' if partner_data['difference'] < 0 else 'متوازن')
        })
    
    return jsonify(result)


@bp.route('/phase/<id>/settle', methods=['POST'])
def settle_phase_route(id):
    """تنفيذ تسوية المرحلة"""
    notes = request.form.get('notes', '').strip()
    
    result = settle_phase(id, notes=notes, created_by='المستخدم')
    
    if result['success']:
        flash(result['message'], 'success')
        return redirect(url_for('settlement.phase_detail', id=id))
    else:
        flash(result['error'], 'error')
        return redirect(url_for('settlement.phase_detail', id=id))


@bp.route('/projects/<project_id>/ledger')
def project_ledger(project_id):
    """دفتر أرصدة الشركاء في المشروع"""
    project = Project.query.get_or_404(project_id)
    ledger_data = get_project_ledger(project_id)
    
    # حساب الإجماليات
    total_debit = sum(item['balance'] for item in ledger_data if item['balance'] > 0)
    total_credit = sum(abs(item['balance']) for item in ledger_data if item['balance'] < 0)
    
    return render_template('settlement/project_ledger.html',
                         project=project,
                         ledger_data=ledger_data,
                         total_debit=total_debit,
                         total_credit=total_credit)


@bp.route('/project-partners')
def project_partners_index():
    """قائمة الشركاء في المشاريع"""
    page = request.args.get('page', 1, type=int)
    project_id = request.args.get('project_id', '')
    
    query = ProjectPartner.query
    
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    query = query.order_by(ProjectPartner.joined_at.desc())
    
    project_partners = query.paginate(page=page, per_page=20, error_out=False)
    projects = Project.query.filter_by(status='نشط').order_by(Project.name).all()
    
    return render_template('settlement/project_partners.html',
                         project_partners=project_partners,
                         projects=projects,
                         project_id=project_id)


@bp.route('/project-partners/add', methods=['POST'])
def add_project_partner():
    """إضافة شريك للمشروع"""
    project_id = request.form.get('project_id')
    partner_id = request.form.get('partner_id')
    share_percentage = float(request.form.get('share_percentage', 0))
    
    # التحقق من عدم وجود الشريك في المشروع
    existing = ProjectPartner.query.filter_by(
        project_id=project_id,
        partner_id=partner_id,
        is_active=True
    ).first()
    
    if existing:
        flash('الشريك موجود بالفعل في هذا المشروع', 'error')
        return redirect(request.referrer or url_for('settlement.project_partners_index'))
    
    pp = ProjectPartner(
        id=generate_uid('PP'),
        project_id=project_id,
        partner_id=partner_id,
        share_percentage=share_percentage
    )
    
    db.session.add(pp)
    log_action('إضافة شريك للمشروع', {'project_id': project_id, 'partner_id': partner_id})
    db.session.commit()
    
    flash('تم إضافة الشريك بنجاح', 'success')
    return redirect(request.referrer or url_for('settlement.project_partners_index'))