from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.materials import bp
from acc.models import Material, ProjectMaterial
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination
from sqlalchemy import func

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    # Base query
    query = Material.query
    
    # Search
    if search:
        query = query.filter(
            db.or_(
                Material.name.ilike(f'%{search}%'),
                Material.unit.ilike(f'%{search}%'),
                Material.description.ilike(f'%{search}%')
            )
        )
    
    # Order by name
    query = query.order_by(Material.name)
    
    # Pagination
    pagination = Pagination(query, page)
    materials = pagination.items
    
    return render_template('materials/index.html',
                         materials=materials,
                         pagination=pagination,
                         search=search)


@bp.route('/<id>')
def detail(id):
    material = Material.query.get_or_404(id)
    
    # Get material usage in projects
    project_materials = ProjectMaterial.query.filter_by(material_id=id).order_by(ProjectMaterial.created_at.desc()).all()
    
    # Calculate statistics
    total_used = db.session.query(func.sum(ProjectMaterial.quantity)).filter_by(material_id=id).scalar() or 0
    total_value = db.session.query(func.sum(ProjectMaterial.total_price)).filter_by(material_id=id).scalar() or 0
    
    return render_template('materials/detail.html',
                         material=material,
                         project_materials=project_materials,
                         total_used=total_used,
                         total_value=total_value)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        unit = request.form.get('unit', '').strip()
        unit_cost = float(request.form.get('unit_cost', 0))
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('الرجاء إدخال اسم المادة', 'error')
            return redirect(url_for('materials.add'))
        
        if not unit:
            flash('الرجاء إدخال وحدة القياس', 'error')
            return redirect(url_for('materials.add'))
        
        material = Material(
            id=generate_uid('M'),
            name=name,
            unit=unit,
            unit_cost=unit_cost if unit_cost else 0,
            description=description
        )
        
        db.session.add(material)
        log_action('إضافة مادة جديدة', {'id': material.id, 'name': material.name})
        db.session.commit()
        
        flash('تم إضافة المادة بنجاح', 'success')
        return redirect(url_for('materials.detail', id=material.id))
    
    return render_template('materials/add.html')


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    material = Material.query.get_or_404(id)
    
    if request.method == 'POST':
        material.name = request.form.get('name', '').strip()
        material.unit = request.form.get('unit', '').strip()
        material.unit_cost = float(request.form.get('unit_cost', 0))
        material.description = request.form.get('description', '').strip()
        
        if not material.name:
            flash('الرجاء إدخال اسم المادة', 'error')
            return redirect(url_for('materials.edit', id=id))
        
        if not material.unit:
            flash('الرجاء إدخال وحدة القياس', 'error')
            return redirect(url_for('materials.edit', id=id))
        
        log_action('تعديل مادة', {'id': material.id, 'name': material.name})
        db.session.commit()
        
        flash('تم تعديل المادة بنجاح', 'success')
        return redirect(url_for('materials.detail', id=id))
    
    return render_template('materials/edit.html', material=material)


@bp.route('/<id>/delete', methods=['POST'])
def delete(id):
    material = Material.query.get_or_404(id)
    
    # Check if material is used in projects
    if material.project_materials.count() > 0:
        flash('لا يمكن حذف المادة لأنها مستخدمة في مشاريع', 'error')
        return redirect(url_for('materials.detail', id=id))
    
    log_action('حذف مادة', {'id': material.id, 'name': material.name})
    db.session.delete(material)
    db.session.commit()
    
    flash('تم حذف المادة بنجاح', 'success')
    return redirect(url_for('materials.index'))


@bp.route('/api/materials')
def api_materials():
    """API endpoint for materials autocomplete"""
    materials = Material.query.order_by(Material.name).all()
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'unit': m.unit,
        'unit_cost': float(m.unit_cost)
    } for m in materials])