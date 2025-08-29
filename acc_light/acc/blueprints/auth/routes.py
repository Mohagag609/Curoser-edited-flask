from flask import render_template, request, redirect, url_for, flash, session
from acc.blueprints.auth import bp
from werkzeug.security import check_password_hash
from acc.services.project_selection import clear_current_project
import os


# مستخدمين تجريبيين (يمكن استبدالهم بقاعدة بيانات لاحقاً)
USERS = {
    'admin': {
        'password': 'pbkdf2:sha256:600000$kR5XWZQN$8c4f6e4d91c0c8b5e8d9e8f8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8',  # admin123
        'name': 'مدير النظام',
        'role': 'admin'
    }
}


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if 'user_id' in session:
        return redirect(url_for('main.select_project'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        
        # للتجربة: قبول admin/admin123
        if username == 'admin' and password == 'admin123':
            session['user_id'] = username
            session['user_name'] = 'مدير النظام'
            session['user_role'] = 'admin'
            
            if remember:
                session.permanent = True
            
            flash('تم تسجيل الدخول بنجاح', 'success')
            
            # توجيه لصفحة اختيار المشروع
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.select_project'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    """تسجيل الخروج"""
    clear_current_project()
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('auth.login'))