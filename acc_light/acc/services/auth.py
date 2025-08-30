from functools import wraps
from flask import session, redirect, url_for, request
import hashlib


def login_required(f):
    """Decorator للتحقق من تسجيل الدخول"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """الحصول على بيانات المستخدم الحالي"""
    if 'user_id' in session:
        return {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'role': session.get('user_role')
        }
    return None


def is_admin():
    """التحقق من أن المستخدم مدير"""
    return session.get('user_role') == 'admin'


def hash_password(password):
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()