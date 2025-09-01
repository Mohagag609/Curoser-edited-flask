from flask import render_template, request, redirect, url_for, flash, session
from acc.blueprints.main import bp
from acc.models import Project
from acc.services.project_selection import get_current_project, clear_current_project
from acc.services.auth import login_required
from acc.extensions import db

@bp.route('/')
def index():
    """الصفحة الرئيسية - الذهاب مباشرة لاختيار المشروع"""
    # تسجيل دخول تلقائي
    if 'user_id' not in session:
        session['user_id'] = 'default-user'
        session['user_name'] = 'المستخدم'
    
    # الذهاب مباشرة لاختيار المشروع
    return redirect(url_for('main.select_project'))

@bp.route('/select-project')
def select_project():
    """صفحة اختيار المشروع"""
    # تسجيل دخول تلقائي إذا لم يكن موجود
    if 'user_id' not in session:
        session['user_id'] = 'default-user'
        session['user_name'] = 'المستخدم'
    
    # الحصول على جميع المشاريع النشطة
    projects = Project.query.filter_by(status='نشط').order_by(Project.name).all()
    current_project = get_current_project()
    
    return render_template('projects/select_simple.html', 
                         projects=projects,
                         current_project=current_project)

@bp.route('/set-project/<project_id>')
def set_project(project_id):
    """تعيين المشروع الحالي"""
    project = Project.query.get_or_404(project_id)
    
    if project.status != 'نشط':
        flash('لا يمكن اختيار مشروع غير نشط', 'error')
        return redirect(url_for('main.select_project'))
    
    # تعيين المشروع مباشرة في الجلسة
    session['current_project_id'] = project_id
    session.permanent = True
    
    flash(f'تم اختيار مشروع: {project.name}', 'success')
    
    # العودة للصفحة المطلوبة أو لوحة التحكم
    next_url = session.pop('next_url', None)
    if next_url:
        return redirect(next_url)
    return redirect(url_for('dashboard.index'))

@bp.route('/clear-project')
def clear_project():
    """مسح المشروع الحالي والعودة لصفحة الاختيار"""
    clear_current_project()
    flash('تم إلغاء اختيار المشروع', 'info')
    return redirect(url_for('main.select_project'))