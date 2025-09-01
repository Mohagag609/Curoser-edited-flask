from flask import render_template, request, redirect, url_for, flash, send_file, jsonify
from acc.blueprints.system import bp
from acc.models import Settings, AuditLog
from acc.extensions import db
from acc.services.utils import log_action, get_today
from acc.services.backup import create_backup, restore_backup, get_backups_list
import os
import json
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

@bp.route('/')
def index():
    """الصفحة الرئيسية للنظام"""
    return redirect(url_for('system.settings'))

@bp.route('/settings', methods=['GET', 'POST'])
def settings():
    """إعدادات النظام"""
    # جلب الإعدادات الحالية أو إنشاء جديدة
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()
    
    if request.method == 'POST':
        # تحديث الإعدادات
        settings.company_name = request.form.get('company_name', '').strip()
        settings.company_address = request.form.get('company_address', '').strip()
        settings.company_phone = request.form.get('company_phone', '').strip()
        settings.company_email = request.form.get('company_email', '').strip()
        settings.tax_number = request.form.get('tax_number', '').strip()
        settings.commercial_register = request.form.get('commercial_register', '').strip()
        
        # إعدادات العملة
        settings.currency_symbol = request.form.get('currency_symbol', 'ج.م').strip()
        settings.currency_position = request.form.get('currency_position', 'after')
        
        # إعدادات النظام
        settings.fiscal_year_start = request.form.get('fiscal_year_start', '01-01')
        settings.default_payment_terms = int(request.form.get('default_payment_terms', 30))
        settings.invoice_prefix = request.form.get('invoice_prefix', 'INV-').strip()
        settings.contract_prefix = request.form.get('contract_prefix', 'CT-').strip()
        
        # إعدادات الإشعارات
        settings.enable_email_notifications = request.form.get('enable_email_notifications') == 'on'
        settings.notification_email = request.form.get('notification_email', '').strip()
        
        # إعدادات النسخ الاحتياطي
        settings.auto_backup_enabled = request.form.get('auto_backup_enabled') == 'on'
        settings.backup_frequency = request.form.get('backup_frequency', 'daily')
        settings.backup_retention_days = int(request.form.get('backup_retention_days', 30))
        
        log_action('تحديث إعدادات النظام', {})
        db.session.commit()
        
        flash('تم حفظ الإعدادات بنجاح', 'success')
        return redirect(url_for('system.settings'))
    
    return render_template('system/settings.html', settings=settings)

@bp.route('/audit-log')
def audit_log():
    """سجل التدقيق"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = AuditLog.query
    
    # البحث
    if search:
        query = query.filter(
            db.or_(
                AuditLog.description.ilike(f'%{search}%'),
                AuditLog.user_id.ilike(f'%{search}%')
            )
        )
    
    # فلترة التاريخ
    if date_from:
        query = query.filter(AuditLog.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(AuditLog.created_at <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    
    # ترتيب حسب الأحدث
    query = query.order_by(AuditLog.created_at.desc())
    
    # صفحات
    logs = query.paginate(page=page, per_page=50, error_out=False)
    
    return render_template('system/audit_log.html', 
                         logs=logs,
                         search=search,
                         date_from=date_from,
                         date_to=date_to)

@bp.route('/backup')
def backup():
    """صفحة النسخ الاحتياطي"""
    backups = get_backups_list()
    return render_template('system/backup.html', backups=backups)

@bp.route('/backup/create', methods=['POST'])
def create_backup_route():
    """إنشاء نسخة احتياطية"""
    try:
        backup_path = create_backup()
        log_action('إنشاء نسخة احتياطية', {'path': backup_path})
        flash('تم إنشاء النسخة الاحتياطية بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ في إنشاء النسخة الاحتياطية: {str(e)}', 'error')
    
    return redirect(url_for('system.backup'))

@bp.route('/backup/download/<filename>')
def download_backup(filename):
    """تحميل نسخة احتياطية"""
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'backups')
    file_path = os.path.join(backup_dir, secure_filename(filename))
    
    if os.path.exists(file_path):
        log_action('تحميل نسخة احتياطية', {'filename': filename})
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        flash('الملف غير موجود', 'error')
        return redirect(url_for('system.backup'))

@bp.route('/backup/restore/<filename>', methods=['POST'])
def restore_backup_route(filename):
    """استعادة نسخة احتياطية"""
    try:
        restore_backup(filename)
        log_action('استعادة نسخة احتياطية', {'filename': filename})
        flash('تم استعادة النسخة الاحتياطية بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ في استعادة النسخة الاحتياطية: {str(e)}', 'error')
    
    return redirect(url_for('system.backup'))

@bp.route('/backup/delete/<filename>', methods=['POST'])
def delete_backup(filename):
    """حذف نسخة احتياطية"""
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'backups')
    file_path = os.path.join(backup_dir, secure_filename(filename))
    
    if os.path.exists(file_path):
        os.remove(file_path)
        log_action('حذف نسخة احتياطية', {'filename': filename})
        flash('تم حذف النسخة الاحتياطية', 'success')
    else:
        flash('الملف غير موجود', 'error')
    
    return redirect(url_for('system.backup'))

@bp.route('/maintenance')
def maintenance():
    """صفحة الصيانة"""
    # معلومات قاعدة البيانات
    db_info = {
        'engine': db.engine.name,
        'url': str(db.engine.url).split('@')[1] if '@' in str(db.engine.url) else str(db.engine.url),
        'tables_count': len(db.metadata.tables),
        'size': get_database_size()
    }
    
    # معلومات النظام
    system_info = {
        'python_version': os.sys.version.split()[0],
        'flask_version': '3.0.0',
        'sqlalchemy_version': '2.0.23',
        'uptime': get_system_uptime()
    }
    
    return render_template('system/maintenance.html', 
                         db_info=db_info,
                         system_info=system_info)

@bp.route('/maintenance/optimize', methods=['POST'])
def optimize_database():
    """تحسين قاعدة البيانات"""
    try:
        # تنظيف السجلات القديمة
        old_date = datetime.now() - timedelta(days=90)
        AuditLog.query.filter(AuditLog.created_at < old_date).delete()
        
        db.session.commit()
        
        log_action('تحسين قاعدة البيانات', {})
        flash('تم تحسين قاعدة البيانات بنجاح', 'success')
    except Exception as e:
        flash(f'خطأ في تحسين قاعدة البيانات: {str(e)}', 'error')
    
    return redirect(url_for('system.maintenance'))

def get_database_size():
    """حساب حجم قاعدة البيانات"""
    try:
        # للـ SQLite
        if 'sqlite' in str(db.engine.url):
            db_path = str(db.engine.url).replace('sqlite:///', '')
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                return f"{size / 1024 / 1024:.2f} MB"
        return "غير متاح"
    except:
        return "غير متاح"

def get_system_uptime():
    """حساب وقت تشغيل النظام"""
    try:
        # يمكن تحسين هذا لاحقاً
        return "متاح"
    except:
        return "غير متاح"