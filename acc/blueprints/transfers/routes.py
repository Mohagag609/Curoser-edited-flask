from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.transfers import bp
from acc.models import Project, Safe, InterProjectTransfer
from acc.services.inter_project_transfer import (
    create_inter_project_transfer, 
    get_project_transfers,
    get_transfer_summary
)
from acc.services.project_selection import get_current_project, project_required
from acc.extensions import db

@bp.route('/')
@project_required
def index():
    """قائمة التحويلات بين المشاريع"""
    current_project = get_current_project()
    transfers = get_project_transfers(current_project.id)
    summary = get_transfer_summary(current_project.id)
    
    return render_template('transfers/index.html',
                         transfers=transfers,
                         summary=summary)

@bp.route('/add', methods=['GET', 'POST'])
@project_required
def add():
    """إضافة تحويل جديد بين المشاريع"""
    current_project = get_current_project()
    
    if request.method == 'POST':
        # المشروع والخزينة المُرسلة (المشروع الحالي)
        from_safe_id = request.form.get('from_safe_id')
        
        # المشروع والخزينة المُستقبلة
        to_project_id = request.form.get('to_project_id')
        to_safe_id = request.form.get('to_safe_id')
        
        amount = float(request.form.get('amount', 0))
        notes = request.form.get('notes')
        
        if amount <= 0:
            flash('المبلغ يجب أن يكون أكبر من صفر', 'error')
            return redirect(url_for('transfers.add'))
        
        success, message, transfer = create_inter_project_transfer(
            from_project_id=current_project.id,
            from_safe_id=from_safe_id,
            to_project_id=to_project_id,
            to_safe_id=to_safe_id,
            amount=amount,
            notes=notes
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('transfers.index'))
        else:
            flash(message, 'error')
    
    # الحصول على المشاريع الأخرى النشطة
    other_projects = Project.query.filter(
        Project.id != current_project.id,
        Project.status == 'نشط'
    ).order_by(Project.name).all()
    
    # خزن المشروع الحالي
    from_safes = Safe.query.filter_by(
        project_id=current_project.id
    ).order_by(Safe.name).all()
    
    return render_template('transfers/add.html',
                         other_projects=other_projects,
                         from_safes=from_safes)

@bp.route('/detail/<id>')
@project_required
def detail(id):
    """عرض تفاصيل التحويل"""
    transfer = InterProjectTransfer.query.get_or_404(id)
    current_project = get_current_project()
    
    # التحقق من أن التحويل مرتبط بالمشروع الحالي
    if transfer.from_project_id != current_project.id and transfer.to_project_id != current_project.id:
        flash('لا يمكنك عرض هذا التحويل', 'error')
        return redirect(url_for('transfers.index'))
    
    return render_template('transfers/detail.html', transfer=transfer)

@bp.route('/api/project-safes/<project_id>')
@project_required
def api_project_safes(project_id):
    """API للحصول على خزن مشروع معين"""
    safes = Safe.query.filter_by(project_id=project_id).order_by(Safe.name).all()
    
    return jsonify([{
        'id': safe.id,
        'name': safe.name,
        'balance': float(safe.balance),
        'type': safe.type
    } for safe in safes])