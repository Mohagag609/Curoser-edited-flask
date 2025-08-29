from flask import session, redirect, url_for, request
from functools import wraps
from acc.models import Project
from acc.services.auth import login_required


def get_current_project_id():
    """الحصول على معرف المشروع الحالي من الجلسة"""
    return session.get('current_project_id')


def set_current_project(project_id):
    """تعيين المشروع الحالي في الجلسة"""
    session['current_project_id'] = project_id
    session.permanent = True


def clear_current_project():
    """مسح المشروع الحالي من الجلسة"""
    session.pop('current_project_id', None)


def project_required(f):
    """Decorator للتحقق من اختيار مشروع قبل الوصول للصفحة"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # الصفحات المستثناة من اختيار المشروع
        exempt_endpoints = [
            'main.index',
            'main.select_project',
            'main.set_project',
            'main.clear_project',
            'static',
            'projects.index',
            'projects.add',
            'projects.edit',
            'projects.delete',
            'projects.api_projects'
        ]
        
        if request.endpoint in exempt_endpoints:
            return f(*args, **kwargs)
            
        if not get_current_project_id():
            # حفظ الصفحة المطلوبة للعودة إليها بعد اختيار المشروع
            session['next_url'] = request.url
            return redirect(url_for('main.select_project'))
            
        # التحقق من وجود المشروع
        project = Project.query.get(get_current_project_id())
        if not project:
            clear_current_project()
            return redirect(url_for('main.select_project'))
            
        return f(*args, **kwargs)
    return decorated_function


def get_current_project():
    """الحصول على كائن المشروع الحالي"""
    project_id = get_current_project_id()
    if project_id:
        return Project.query.get(project_id)
    return None