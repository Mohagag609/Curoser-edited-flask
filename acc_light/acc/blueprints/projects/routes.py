from flask import render_template, request, redirect, url_for, flash
from acc.blueprints.projects import bp
from acc.models import Project, ProjectStage, Contractor, Unit
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination, parse_number, get_today
from acc.services.project_context import set_current_project
from datetime import datetime

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    # Base query
    query = Project.query
    
    # Search
    if search:
        query = query.filter(
            db.or_(
                Project.name.ilike(f'%{search}%'),
                Project.description.ilike(f'%{search}%')
            )
        )
    
    # Filter by status
    if status:
        query = query.filter(Project.status == status)
    
    # Order by start date desc
    query = query.order_by(Project.start_date.desc())
    
    # Pagination
    pagination = Pagination(query, page)
    projects = pagination.items
    
    # Calculate stats
    total_projects = Project.query.count()
    active_projects = Project.query.filter_by(status='جاري').count()
    completed_projects = Project.query.filter_by(status='مكتمل').count()
    
    return render_template('projects/index.html',
                         projects=projects,
                         pagination=pagination,
                         search=search,
                         status=status,
                         total_projects=total_projects,
                         active_projects=active_projects,
                         completed_projects=completed_projects)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        project_type = request.form.get('project_type', 'عقاري')
        budget = parse_number(request.form.get('budget', 0))
        start_date = request.form.get('start_date', '').strip()
        expected_end_date = request.form.get('expected_end_date', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('الرجاء إدخال اسم المشروع', 'error')
            return redirect(url_for('projects.add'))
        
        if not code:
            flash('الرجاء إدخال كود المشروع', 'error')
            return redirect(url_for('projects.add'))
        
        # Check if code already exists
        existing = Project.query.filter_by(code=code).first()
        if existing:
            flash('كود المشروع موجود بالفعل', 'error')
            return redirect(url_for('projects.add'))
        
        project = Project(
            id=generate_uid('PRJ'),
            name=name,
            code=code,
            project_type=project_type,
            budget=budget if budget > 0 else None,
            start_date=datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None,
            expected_end_date=datetime.strptime(expected_end_date, '%Y-%m-%d').date() if expected_end_date else None,
            description=description,
            status='نشط'
        )
        
        try:
            db.session.add(project)
            log_action('إضافة مشروع جديد', {'id': project.id, 'name': project.name})
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'خطأ في حفظ المشروع: {str(e)}', 'error')
            return redirect(url_for('projects.add'))
        
        flash('تم إضافة المشروع بنجاح', 'success')
        
        # اختيار المشروع الجديد مباشرة
        set_current_project(project.id)
        
        # التوجيه للوحة التحكم
        return redirect('/dashboard')
    
    # Get data for form
    return render_template('projects/add.html',
                         today=get_today())


@bp.route('/<id>')
def detail(id):
    project = Project.query.get_or_404(id)
    
    # Get project stages
    stages = project.stages.order_by(ProjectStage.created_at).all()
    
    # Calculate progress
    if stages:
        completed_stages = sum(1 for s in stages if s.status == 'مكتمل')
        progress = (completed_stages / len(stages)) * 100
    else:
        progress = 0
    
    # Calculate costs
    total_spent = sum(s.cost or 0 for s in stages)
    
    return render_template('projects/detail.html',
                         project=project,
                         stages=stages,
                         progress=progress,
                         total_spent=total_spent)


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    project = Project.query.get_or_404(id)
    
    if request.method == 'POST':
        project.name = request.form.get('name', '').strip()
        project.code = request.form.get('code', '').strip()
        project.project_type = request.form.get('project_type', 'عقاري')
        project.budget = parse_number(request.form.get('budget', 0)) or None
        start_date = request.form.get('start_date', '')
        project.start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        expected_end_date = request.form.get('expected_end_date', '')
        project.expected_end_date = datetime.strptime(expected_end_date, '%Y-%m-%d').date() if expected_end_date else None
        actual_end_date = request.form.get('actual_end_date', '')
        project.actual_end_date = datetime.strptime(actual_end_date, '%Y-%m-%d').date() if actual_end_date else None
        project.status = request.form.get('status', 'نشط')
        project.description = request.form.get('description', '').strip()
        project.is_default = request.form.get('is_default') == '1'
        
        if not project.name:
            flash('الرجاء إدخال اسم المشروع', 'error')
            return redirect(url_for('projects.edit', id=id))
        
        if not project.code:
            flash('الرجاء إدخال كود المشروع', 'error')
            return redirect(url_for('projects.edit', id=id))
        
        # Check if code already exists (excluding current project)
        existing = Project.query.filter(Project.code == project.code, Project.id != project.id).first()
        if existing:
            flash('كود المشروع موجود بالفعل', 'error')
            return redirect(url_for('projects.edit', id=id))
        
        # If marking as default, unset other defaults
        if project.is_default:
            Project.query.filter(Project.id != project.id).update({'is_default': False})
        
        log_action('تعديل مشروع', {'id': project.id, 'name': project.name})
        db.session.commit()
        
        flash('تم تحديث بيانات المشروع بنجاح', 'success')
        return redirect(url_for('projects.detail', id=id))
    
    return render_template('projects/edit.html', project=project)


@bp.route('/<id>/add-stage', methods=['POST'])
def add_stage(id):
    project = Project.query.get_or_404(id)
    
    name = request.form.get('name', '').strip()
    stage_number = request.form.get('stage_number', type=int)
    estimated_cost = parse_number(request.form.get('estimated_cost', 0))
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('الرجاء إدخال اسم المرحلة', 'error')
        return redirect(url_for('projects.detail', id=id))
    
    stage = ProjectStage(
            id=generate_uid('PS'),
            project_id=id,
        name=name,
        stage_number=stage_number or (project.stages.count() + 1),
        estimated_cost=estimated_cost if estimated_cost > 0 else None,
        description=description,
        status='جديد'
    )
    
    db.session.add(stage)
    log_action('إضافة مرحلة مشروع', {
        'project_id': id,
        'stage_name': name
    })
    db.session.commit()
    
    flash('تم إضافة المرحلة بنجاح', 'success')
    return redirect(url_for('projects.detail', id=id))


@bp.route('/<project_id>/update-stage/<stage_id>', methods=['POST'])
def update_stage(project_id, stage_id):
    stage = ProjectStage.query.get_or_404(stage_id)
    
    if stage.project_id != project_id:
        flash('خطأ في البيانات', 'error')
        return redirect(url_for('projects.detail', id=project_id))
    
    stage.status = request.form.get('status', 'جديد')
    stage.actual_cost = parse_number(request.form.get('actual_cost', 0)) or None
    stage.notes = request.form.get('notes', '').strip()
    
    # Set dates based on status
    if stage.status == 'جاري' and not stage.start_date:
        stage.start_date = get_today()
    elif stage.status == 'مكتمل' and not stage.end_date:
        stage.end_date = get_today()
    
    log_action('تحديث مرحلة مشروع', {
        'stage_id': stage_id,
        'status': stage.status
    })
    db.session.commit()
    
    flash('تم تحديث المرحلة بنجاح', 'success')
    return redirect(url_for('projects.detail', id=project_id))

@bp.route('/set-project/<string:project_id>')
def set_project(project_id):
    """Set the current project"""
    if set_current_project(project_id):
        project = Project.query.get(project_id)
        flash(f'تم تحديد المشروع: {project.name}', 'success')
    else:
        flash('خطأ في تحديد المشروع', 'error')
    
    # Redirect to the previous page or dashboard
    return redirect(request.referrer or url_for('dashboard.index'))