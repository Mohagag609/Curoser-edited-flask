"""
Decorators for the application
"""
from functools import wraps
from flask import redirect, url_for, session, flash, request, g
from acc.models import Project
from acc.services.project_selection import get_current_project


def login_required(f):
    """يتطلب تسجيل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('الرجاء تسجيل الدخول أولاً.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def project_required(f):
    """يتطلب اختيار مشروع"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_project = get_current_project()
        if not current_project:
            flash('الرجاء اختيار مشروع أولاً.', 'warning')
            return redirect(url_for('main.select_project', next=request.url))
        g.project = current_project  # Attach project to global context
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """يتطلب صلاحيات المسؤول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('الرجاء تسجيل الدخول أولاً.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        # Add admin check here if needed
        return f(*args, **kwargs)
    return decorated_function