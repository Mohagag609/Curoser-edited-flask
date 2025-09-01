"""خدمات النسخ الاحتياطي والاستعادة"""
import os
import json
import shutil
import zipfile
from datetime import datetime
from flask import current_app
from acc.extensions import db
from acc.models import *
import tempfile


def create_backup():
    """إنشاء نسخة احتياطية من قاعدة البيانات"""
    # إنشاء مجلد النسخ الاحتياطي إذا لم يكن موجوداً
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # اسم ملف النسخة الاحتياطية
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'backup_{timestamp}.zip'
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # إنشاء مجلد مؤقت
    with tempfile.TemporaryDirectory() as temp_dir:
        # تصدير البيانات إلى JSON
        export_data_to_json(temp_dir)
        
        # نسخ قاعدة البيانات إذا كانت SQLite
        if 'sqlite' in str(db.engine.url):
            db_path = str(db.engine.url).replace('sqlite:///', '')
            if os.path.exists(db_path):
                shutil.copy2(db_path, os.path.join(temp_dir, 'database.db'))
        
        # إنشاء ملف ZIP
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
    
    return backup_path


def restore_backup(filename):
    """استعادة نسخة احتياطية"""
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
    backup_path = os.path.join(backup_dir, filename)
    
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {filename}")
    
    # إنشاء مجلد مؤقت لاستخراج الملفات
    with tempfile.TemporaryDirectory() as temp_dir:
        # استخراج الملفات
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(temp_dir)
        
        # استعادة البيانات من JSON
        import_data_from_json(temp_dir)
    
    return True


def get_backups_list():
    """الحصول على قائمة النسخ الاحتياطية"""
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.endswith('.zip'):
            file_path = os.path.join(backup_dir, filename)
            stat = os.stat(file_path)
            backups.append({
                'filename': filename,
                'size': stat.st_size,
                'size_mb': f"{stat.st_size / 1024 / 1024:.2f}",
                'created': datetime.fromtimestamp(stat.st_mtime),
                'created_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    # ترتيب حسب الأحدث
    backups.sort(key=lambda x: x['created'], reverse=True)
    return backups


def export_data_to_json(export_dir):
    """تصدير البيانات إلى ملفات JSON"""
    # قائمة النماذج للتصدير
    models_to_export = [
        (Customer, 'customers.json'),
        (Unit, 'units.json'),
        (Partner, 'partners.json'),
        (PartnerGroup, 'partner_groups.json'),
        (Contract, 'contracts.json'),
        (Installment, 'installments.json'),
        (Payment, 'payments.json'),
        (Safe, 'safes.json'),
        (SafeTransfer, 'transfers.json'),
        (Voucher, 'vouchers.json'),
        (Broker, 'brokers.json'),
        (Supplier, 'suppliers.json'),
        (Contractor, 'contractors.json'),
        (Project, 'projects.json'),
        (Material, 'materials.json'),
        (Phase, 'phases.json'),
        (Expense, 'expenses.json'),
        (MaterialIssue, 'material_issues.json'),
        (Settings, 'settings.json'),
        (AuditLog, 'audit_logs.json')
    ]
    
    for model, filename in models_to_export:
        try:
            data = []
            for item in model.query.all():
                item_dict = {}
                for column in item.__table__.columns:
                    value = getattr(item, column.name)
                    # تحويل التواريخ إلى string
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    elif hasattr(value, 'to_dict'):
                        value = value.to_dict()
                    item_dict[column.name] = value
                data.append(item_dict)
            
            # حفظ البيانات
            file_path = os.path.join(export_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error exporting {model.__name__}: {str(e)}")


def import_data_from_json(import_dir):
    """استيراد البيانات من ملفات JSON"""
    # قائمة النماذج للاستيراد (بالترتيب الصحيح للـ foreign keys)
    models_to_import = [
        (Settings, 'settings.json'),
        (Customer, 'customers.json'),
        (Project, 'projects.json'),
        (Partner, 'partners.json'),
        (PartnerGroup, 'partner_groups.json'),
        (Unit, 'units.json'),
        (Broker, 'brokers.json'),
        (Supplier, 'suppliers.json'),
        (Contractor, 'contractors.json'),
        (Material, 'materials.json'),
        (Safe, 'safes.json'),
        (Contract, 'contracts.json'),
        (Installment, 'installments.json'),
        (Payment, 'payments.json'),
        (SafeTransfer, 'transfers.json'),
        (Voucher, 'vouchers.json'),
        (Phase, 'phases.json'),
        (Expense, 'expenses.json'),
        (MaterialIssue, 'material_issues.json'),
        (AuditLog, 'audit_logs.json')
    ]
    
    # حذف البيانات الحالية
    db.drop_all()
    db.create_all()
    
    for model, filename in models_to_import:
        try:
            file_path = os.path.join(import_dir, filename)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item_dict in data:
                    # تحويل التواريخ من string
                    for key, value in item_dict.items():
                        if value and isinstance(value, str) and 'T' in value:
                            try:
                                item_dict[key] = datetime.fromisoformat(value)
                            except:
                                pass
                    
                    # إنشاء الكائن
                    item = model(**item_dict)
                    db.session.add(item)
                
                db.session.commit()
                print(f"Imported {len(data)} records for {model.__name__}")
        except Exception as e:
            print(f"Error importing {model.__name__}: {str(e)}")
            db.session.rollback()


def auto_backup():
    """نسخ احتياطي تلقائي (يمكن استخدامه مع cron job)"""
    settings = Settings.query.first()
    if settings and settings.auto_backup_enabled:
        try:
            backup_path = create_backup()
            
            # حذف النسخ القديمة
            if settings.backup_retention_days > 0:
                cleanup_old_backups(settings.backup_retention_days)
            
            return backup_path
        except Exception as e:
            print(f"Auto backup failed: {str(e)}")
            return None
    return None


def cleanup_old_backups(retention_days):
    """حذف النسخ الاحتياطية القديمة"""
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
    cutoff_date = datetime.now().timestamp() - (retention_days * 86400)
    
    for filename in os.listdir(backup_dir):
        if filename.endswith('.zip'):
            file_path = os.path.join(backup_dir, filename)
            if os.path.getmtime(file_path) < cutoff_date:
                os.remove(file_path)