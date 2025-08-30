#!/usr/bin/env python3
"""
سكريبت لتنظيف وصيانة قاعدة البيانات
"""
from acc import create_app
from acc.extensions import db
from acc.models import AuditLog, Voucher
from datetime import datetime, timedelta
from sqlalchemy import func

def cleanup_old_logs(days=90):
    """حذف السجلات القديمة"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    try:
        old_logs = AuditLog.query.filter(AuditLog.created_at < cutoff_date).count()
        if old_logs > 0:
            AuditLog.query.filter(AuditLog.created_at < cutoff_date).delete()
            db.session.commit()
            print(f"✅ تم حذف {old_logs} سجل قديم")
        else:
            print("✅ لا توجد سجلات قديمة")
    except Exception as e:
        db.session.rollback()
        print(f"❌ خطأ في حذف السجلات: {e}")

def optimize_database():
    """تحسين أداء قاعدة البيانات"""
    try:
        # VACUUM for SQLite
        if 'sqlite' in db.engine.url.drivername:
            db.engine.execute("VACUUM")
            print("✅ تم تحسين قاعدة البيانات SQLite")
        # ANALYZE for PostgreSQL
        elif 'postgresql' in db.engine.url.drivername:
            db.engine.execute("ANALYZE")
            print("✅ تم تحليل قاعدة البيانات PostgreSQL")
    except Exception as e:
        print(f"❌ خطأ في تحسين قاعدة البيانات: {e}")

def check_orphaned_records():
    """البحث عن سجلات يتيمة"""
    issues = []
    
    # فحص الإيصالات بدون خزينة
    orphaned_vouchers = Voucher.query.filter(
        Voucher.safe_id.isnot(None),
        ~Voucher.safe.has()
    ).count()
    
    if orphaned_vouchers > 0:
        issues.append(f"⚠️ {orphaned_vouchers} إيصال بدون خزينة")
    
    if issues:
        print("\nمشاكل تحتاج لمراجعة:")
        for issue in issues:
            print(issue)
    else:
        print("✅ لا توجد سجلات يتيمة")

def main():
    app = create_app()
    
    with app.app_context():
        print("🔧 بدء صيانة قاعدة البيانات...")
        print("-" * 50)
        
        # تنظيف السجلات القديمة
        cleanup_old_logs()
        
        # فحص السجلات اليتيمة
        check_orphaned_records()
        
        # تحسين قاعدة البيانات
        optimize_database()
        
        print("-" * 50)
        print("✅ اكتملت الصيانة بنجاح!")

if __name__ == '__main__':
    main()