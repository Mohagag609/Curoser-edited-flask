from flask import render_template, request, redirect, url_for, flash, jsonify, session
from acc.blueprints.projects import bp
from acc.models import Project, ProjectStage, Unit
from acc.models.contractor import Contractor
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination, parse_number, get_today, format_currency
from acc.services.project_selection import set_current_project
from acc.services.code_generator import generate_project_code
from sqlalchemy import func, or_

@bp.route('/')
def index():
    # التحقق من تسجيل الدخول
    if 'user_id' not in session:
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    project_type = request.args.get('project_type', '')
    
    # Base query
    query = Project.query
    
    # Search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Project.name.ilike(search_term),
                Project.code.ilike(search_term),
                Project.description.ilike(search_term),
                Project.location.ilike(search_term)
            )
        )
    
    # Filter by status
    if status:
        query = query.filter(Project.status == status)
    
    # Filter by type
    if project_type:
        query = query.filter(Project.project_type == project_type)
    
    # Order by created date desc
    query = query.order_by(Project.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    projects = pagination.items
    
    # Calculate stats
    total_projects = Project.query.count()
    active_projects = Project.query.filter_by(status='نشط').count()
    completed_projects = Project.query.filter_by(status='مكتمل').count()
    
    return render_template('projects/index.html',
                         projects=projects,
                         pagination=pagination,
                         q=q,
                         status=status,
                         project_type=project_type,
                         total_projects=total_projects,
                         active_projects=active_projects,
                         completed_projects=completed_projects)

@bp.route('/search')
def search():
    """Advanced search endpoint for AJAX"""
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    project_type = request.args.get('project_type', '')
    page = request.args.get('page', 1, type=int)
    
    query = Project.query
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Project.name.ilike(search_term),
                Project.code.ilike(search_term),
                Project.description.ilike(search_term),
                Project.location.ilike(search_term)
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Project.status == status)
    
    # Type filter
    if project_type:
        query = query.filter(Project.project_type == project_type)
    
    # Order by
    query = query.order_by(Project.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Calculate stats
    total_projects = Project.query.count()
    active_projects = Project.query.filter_by(status='نشط').count()
    completed_projects = Project.query.filter_by(status='مكتمل').count()
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('projects/_results.html',
                             projects=pagination.items,
                             pagination=pagination,
                             q=q,
                             status=status,
                             project_type=project_type)
    
    return render_template('projects/index.html',
                         projects=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status,
                         project_type=project_type,
                         total_projects=total_projects,
                         active_projects=active_projects,
                         completed_projects=completed_projects)

@bp.route('/<id>')
def detail(id):
    project = Project.query.get_or_404(id)
    
    # Get stages
    stages = ProjectStage.query.filter_by(project_id=id).order_by(ProjectStage.order_num).all()
    
    # Calculate stats
    total_units = Unit.query.filter_by(project_id=id).count()
    sold_units = Unit.query.filter_by(project_id=id, status='مباعة').count()
    available_units = Unit.query.filter_by(project_id=id, status='متاحة').count()
    
    return render_template('projects/detail.html',
                         project=project,
                         stages=stages,
                         total_units=total_units,
                         sold_units=sold_units,
                         available_units=available_units)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        project_type = request.form.get('project_type', 'عقاري')
        location = request.form.get('location', '').strip()
        area = request.form.get('area', '').strip()
        budget = parse_number(request.form.get('budget', 0))
        contractor_id = request.form.get('contractor_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        status = request.form.get('status', 'نشط')
        description = request.form.get('description', '').strip()
        
        if not name:
            error_msg = 'الرجاء إدخال اسم المشروع'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('projects.add'))
        
        # Check for duplicate name
        existing = Project.query.filter_by(name=name).first()
        if existing:
            error_msg = f'مشروع بنفس الاسم "{name}" موجود بالفعل'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': f'⚠️ {error_msg}',
                    'redirect': url_for('projects.detail', id=existing.id)
                }), 400
            
            flash(f'⚠️ {error_msg}', 'warning')
            return redirect(url_for('projects.detail', id=existing.id))
        
        try:
            # Generate code automatically
            code = generate_project_code()
            
            project = Project(
                id=generate_uid('PRJ'),
                name=name,
                code=code,
                project_type=project_type,
                location=location,
                area=area,
                budget=budget,
                contractor_id=contractor_id if contractor_id else None,
                start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
                expected_end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None,
                status=status,
                description=description
            )
            
            db.session.add(project)
            log_action('إنشاء مشروع جديد', {'id': project.id, 'name': project.name})
            db.session.commit()
            
            # Set as current project if it's the only one
            if Project.query.count() == 1:
                set_current_project(project.id)
            
            success_msg = f'تم إنشاء المشروع بنجاح! رقم المشروع: {code}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('main.select_project')
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('main.select_project'))
            
        except Exception as e:
            db.session.rollback()
            import traceback
            error_details = traceback.format_exc()
            print(f"Project creation error: {error_details}")
            
            error_msg = f'حدث خطأ أثناء إنشاء المشروع: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('projects.add'))
    
    contractors = Contractor.query.order_by(Contractor.name).all()
    return render_template('projects/add.html', contractors=contractors, datetime=datetime)

@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    project = Project.query.get_or_404(id)
    
    if request.method == 'POST':
        project.name = request.form.get('name', '').strip()
        project.project_type = request.form.get('project_type', project.project_type)
        project.location = request.form.get('location', '').strip()
        project.area = request.form.get('area', '').strip()
        project.budget = parse_number(request.form.get('budget', 0))
        project.contractor_id = request.form.get('contractor_id') or None
        
        start_date = request.form.get('start_date')
        if start_date:
            project.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        end_date = request.form.get('end_date')
        if end_date:
            project.expected_end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        project.status = request.form.get('status', project.status)
        project.description = request.form.get('description', '').strip()
        
        if not project.name:
            error_msg = 'الرجاء إدخال اسم المشروع'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('projects.edit', id=id))
        
        # Check for duplicate name (excluding current project)
        existing = Project.query.filter(
            Project.name == project.name,
            Project.id != project.id
        ).first()
        
        if existing:
            error_msg = f'مشروع آخر بنفس الاسم "{project.name}" موجود بالفعل'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': f'⚠️ {error_msg}',
                    'redirect': url_for('projects.detail', id=existing.id)
                }), 400
            
            flash(f'⚠️ {error_msg}', 'warning')
            return redirect(url_for('projects.edit', id=id))
        
        try:
            log_action('تعديل مشروع', {'id': project.id, 'name': project.name})
            db.session.commit()
            
            success_msg = 'تم تعديل المشروع بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('projects.detail', id=id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('projects.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء تعديل المشروع: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('projects.edit', id=id))
    
    contractors = Contractor.query.order_by(Contractor.name).all()
    return render_template('projects/edit.html', project=project, contractors=contractors)

@bp.route('/<id>/delete', methods=['POST'])
def delete(id):
    try:
        project = Project.query.get_or_404(id)
        
        # Check if project has units
        if project.units.count() > 0:
            error_msg = f'لا يمكن حذف المشروع "{project.name}" لأنه يحتوي على وحدات'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('projects.detail', id=id))
        
        project_name = project.name
        project_id = project.id
        
        db.session.delete(project)
        db.session.commit()
        
        log_action('حذف مشروع', {'id': project_id, 'name': project_name})
        
        success_msg = f'تم حذف المشروع "{project_name}" بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'✅ {success_msg}'
            })
        
        flash(f'✅ {success_msg}', 'success')
        return redirect(url_for('projects.index'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'خطأ في حذف المشروع: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
        
        flash(f'❌ {error_msg}', 'error')
        return redirect(url_for('projects.index'))

@bp.route('/api/projects')
def api_projects():
    """API endpoint for projects"""
    projects = Project.query.filter_by(status='نشط').order_by(Project.name).all()
    return jsonify([{
        'id': p.id,
        'code': p.code,
        'name': p.name,
        'type': p.project_type,
        'status': p.status
    } for p in projects])