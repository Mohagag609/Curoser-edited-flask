from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.materials import bp
from acc.models import Material, ProjectMaterial, Project
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from acc.services.code_generator import generate_material_code
from sqlalchemy import func, or_

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    category = request.args.get('category', '')
    
    # Base query
    query = Material.query
    
    # Search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Material.name.ilike(search_term),
                Material.code.ilike(search_term),
                Material.unit.ilike(search_term),
                Material.category.ilike(search_term),
                Material.description.ilike(search_term)
            )
        )
    
    # Filter by category
    if category:
        query = query.filter(Material.category == category)
    
    # Order by created date desc
    query = query.order_by(Material.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    materials = pagination.items
    
    # Get unique categories for filter
    categories = db.session.query(Material.category).distinct().filter(Material.category.isnot(None)).all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('materials/index.html',
                         materials=materials,
                         pagination=pagination,
                         q=q,
                         category=category,
                         categories=categories)

@bp.route('/search')
def search():
    """Advanced search endpoint for AJAX"""
    q = request.args.get('q', '')
    category = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    
    query = Material.query
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Material.name.ilike(search_term),
                Material.code.ilike(search_term),
                Material.unit.ilike(search_term),
                Material.category.ilike(search_term),
                Material.description.ilike(search_term)
            )
        )
    
    # Category filter
    if category:
        query = query.filter(Material.category == category)
    
    # Order by
    query = query.order_by(Material.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Get unique categories
    categories = db.session.query(Material.category).distinct().filter(Material.category.isnot(None)).all()
    categories = [c[0] for c in categories if c[0]]
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('materials/_results.html',
                             materials=pagination.items,
                             pagination=pagination,
                             q=q,
                             category=category,
                             categories=categories)
    
    return render_template('materials/index.html',
                         materials=pagination.items,
                         pagination=pagination,
                         q=q,
                         category=category,
                         categories=categories)

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
        unit_cost = request.form.get('unit_cost', 0)
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        min_stock = request.form.get('min_stock', 0)
        
        # Validation
        if not name:
            error_msg = 'اسم المادة مطلوب'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.add'))
        
        if not unit:
            error_msg = 'وحدة القياس مطلوبة'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.add'))
        
        try:
            material = Material(
                id=generate_uid('MAT'),
                code=generate_material_code(),
                name=name,
                unit=unit,
                unit_cost=float(unit_cost) if unit_cost else 0,
                category=category,
                description=description,
                min_stock=float(min_stock) if min_stock else 0,
                current_stock=0
            )
            
            db.session.add(material)
            log_action('إضافة مادة جديدة', {'id': material.id, 'name': material.name})
            db.session.commit()
            
            success_msg = f'تم إضافة المادة بنجاح! رقم المادة: {material.code}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('materials.detail', id=material.id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('materials.detail', id=material.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء إضافة المادة: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.add'))
    
    return render_template('materials/add.html')

@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    material = Material.query.get_or_404(id)
    
    if request.method == 'POST':
        material.name = request.form.get('name', '').strip()
        material.unit = request.form.get('unit', '').strip()
        material.unit_cost = float(request.form.get('unit_cost', 0))
        material.category = request.form.get('category', '').strip()
        material.description = request.form.get('description', '').strip()
        material.min_stock = float(request.form.get('min_stock', 0))
        
        if not material.name:
            error_msg = 'اسم المادة مطلوب'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.edit', id=id))
        
        if not material.unit:
            error_msg = 'وحدة القياس مطلوبة'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.edit', id=id))
        
        try:
            log_action('تعديل مادة', {'id': material.id, 'name': material.name})
            db.session.commit()
            
            success_msg = 'تم تعديل المادة بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('materials.detail', id=id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('materials.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء تعديل المادة: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.edit', id=id))
    
    return render_template('materials/edit.html', material=material)

@bp.route('/<id>/delete', methods=['POST'])
def delete(id):
    try:
        material = Material.query.get_or_404(id)
        
        # Check if material is used in projects
        if material.project_uses.count() > 0:
            error_msg = f'لا يمكن حذف المادة "{material.name}" لأنها مستخدمة في مشاريع'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.detail', id=id))
        
        material_name = material.name
        material_id = material.id
        
        db.session.delete(material)
        db.session.commit()
        
        log_action('حذف مادة', {'id': material_id, 'name': material_name})
        
        success_msg = f'تم حذف المادة "{material_name}" بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'✅ {success_msg}'
            })
        
        flash(f'✅ {success_msg}', 'success')
        return redirect(url_for('materials.index'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'خطأ في حذف المادة: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
        
        flash(f'❌ {error_msg}', 'error')
        return redirect(url_for('materials.index'))

@bp.route('/api/materials')
def api_materials():
    """API endpoint for materials autocomplete"""
    materials = Material.query.order_by(Material.name).all()
    return jsonify([{
        'id': m.id,
        'code': m.code,
        'name': m.name,
        'unit': m.unit,
        'unit_cost': float(m.unit_cost) if m.unit_cost else 0,
        'category': m.category
    } for m in materials])