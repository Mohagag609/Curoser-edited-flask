from flask import render_template, request, redirect, url_for, flash, jsonify, Response, send_file, session
from acc.blueprints.projects import bp
from acc.models import Project, ProjectStage, Unit
from acc.models.contractor import Contractor
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination, parse_number, get_today, format_currency
from acc.services.project_selection import set_current_project
from acc.services.code_generator import generate_project_code
from acc.services.import_handler import ImportHandler
from sqlalchemy import func, or_
from datetime import datetime
import io
import csv
import json

@bp.route('/')
def index():
    # التحقق من تسجيل الدخول
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
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
                end_date=datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None,
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
                    'redirect': url_for('projects.detail', id=project.id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('projects.detail', id=project.id))
            
        except Exception as e:
            db.session.rollback()
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
            project.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
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


@bp.route('/export/<format>')
def export(format):
    """تصدير بيانات المشاريع"""
    projects = Project.query.order_by(Project.name).all()
    
    if format == 'excel':
        # Generate Excel file (HTML table format)
        output = io.StringIO()
        output.write('<html><head><meta charset="utf-8"></head><body>')
        output.write('<table border="1">')
        output.write('<tr>')
        output.write('<th>رقم المشروع</th>')
        output.write('<th>اسم المشروع</th>')
        output.write('<th>النوع</th>')
        output.write('<th>الموقع</th>')
        output.write('<th>المساحة</th>')
        output.write('<th>الميزانية</th>')
        output.write('<th>المقاول</th>')
        output.write('<th>تاريخ البداية</th>')
        output.write('<th>تاريخ النهاية</th>')
        output.write('<th>الحالة</th>')
        output.write('<th>الوصف</th>')
        output.write('</tr>')
        
        for project in projects:
            output.write('<tr>')
            output.write(f'<td>{project.code}</td>')
            output.write(f'<td>{project.name}</td>')
            output.write(f'<td>{project.project_type}</td>')
            output.write(f'<td>{project.location or "-"}</td>')
            output.write(f'<td>{project.area or "-"}</td>')
            output.write(f'<td>{format_currency(project.budget)}</td>')
            output.write(f'<td>{project.contractor.name if project.contractor else "-"}</td>')
            output.write(f'<td>{project.start_date.strftime("%Y-%m-%d") if project.start_date else "-"}</td>')
            output.write(f'<td>{project.end_date.strftime("%Y-%m-%d") if project.end_date else "-"}</td>')
            output.write(f'<td>{project.status}</td>')
            output.write(f'<td>{project.description or "-"}</td>')
            output.write('</tr>')
        
        output.write('</table></body></html>')
        
        response = Response(output.getvalue(), mimetype='application/vnd.ms-excel')
        response.headers['Content-Disposition'] = f'attachment; filename=projects_{datetime.now().strftime("%Y%m%d")}.xls'
        return response
    
    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['رقم المشروع', 'اسم المشروع', 'النوع', 'الموقع', 'المساحة', 'الميزانية', 'المقاول', 'تاريخ البداية', 'تاريخ النهاية', 'الحالة', 'الوصف'])
        
        # Write data
        for project in projects:
            writer.writerow([
                project.code,
                project.name,
                project.project_type,
                project.location or '-',
                project.area or '-',
                project.budget or 0,
                project.contractor.name if project.contractor else '-',
                project.start_date.strftime('%Y-%m-%d') if project.start_date else '-',
                project.end_date.strftime('%Y-%m-%d') if project.end_date else '-',
                project.status,
                project.description or '-'
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'projects_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    
    elif format == 'json':
        data = []
        for project in projects:
            data.append({
                'code': project.code,
                'name': project.name,
                'type': project.project_type,
                'location': project.location,
                'area': project.area,
                'budget': float(project.budget) if project.budget else 0,
                'contractor': project.contractor.name if project.contractor else None,
                'start_date': project.start_date.isoformat() if project.start_date else None,
                'end_date': project.end_date.isoformat() if project.end_date else None,
                'status': project.status,
                'description': project.description
            })
        
        return jsonify({
            'export_date': datetime.now().isoformat(),
            'total_count': len(data),
            'projects': data
        })
    
    else:
        flash('صيغة التصدير غير مدعومة', 'error')
        return redirect(url_for('projects.index'))


@bp.route('/report')
def report():
    """عرض صفحة التقارير"""
    # إحصائيات عامة
    total_projects = Project.query.count()
    active_projects = Project.query.filter_by(status='نشط').count()
    completed_projects = Project.query.filter_by(status='مكتمل').count()
    paused_projects = Project.query.filter_by(status='متوقف').count()
    
    # إحصائيات حسب النوع
    real_estate_projects = Project.query.filter_by(project_type='عقاري').count()
    accounting_projects = Project.query.filter_by(project_type='محاسبي').count()
    
    # المشاريع الأخيرة
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(10).all()
    
    # المشاريع بالميزانية الأكبر
    top_budget_projects = Project.query.order_by(Project.budget.desc()).limit(10).all()
    
    # إحصائيات الوحدات للمشاريع العقارية
    unit_stats = []
    real_estate = Project.query.filter_by(project_type='عقاري').all()
    for project in real_estate:
        total_units = project.units.count()
        sold_units = project.units.filter_by(status='مباعة').count()
        available_units = project.units.filter_by(status='متاحة').count()
        
        unit_stats.append({
            'project': project,
            'total': total_units,
            'sold': sold_units,
            'available': available_units,
            'occupancy_rate': (sold_units / total_units * 100) if total_units > 0 else 0
        })
    
    return render_template('projects/report.html',
                         total_projects=total_projects,
                         active_projects=active_projects,
                         completed_projects=completed_projects,
                         paused_projects=paused_projects,
                         real_estate_projects=real_estate_projects,
                         accounting_projects=accounting_projects,
                         recent_projects=recent_projects,
                         top_budget_projects=top_budget_projects,
                         unit_stats=unit_stats)


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