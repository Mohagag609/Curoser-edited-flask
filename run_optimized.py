#!/usr/bin/env python3
"""
سكريبت تشغيل النظام المحسن
"""
import os
import sys
from acc import create_app
from acc.core.database import get_database_stats
from acc.core.backup import create_automatic_backup
from acc.core.logging import get_logger

logger = get_logger(__name__)

def main():
    """تشغيل النظام المحسن"""
    print("🚀 بدء تشغيل النظام المحسن...")
    
    # إنشاء التطبيق
    app = create_app()
    
    with app.app_context():
        # عرض إحصائيات قاعدة البيانات
        try:
            stats = get_database_stats()
            print("\n📊 إحصائيات قاعدة البيانات:")
            for table, count in stats.items():
                if not table.startswith('database_'):
                    print(f"   {table}: {count:,} سجل")
            
            if 'database_size_mb' in stats:
                print(f"   حجم قاعدة البيانات: {stats['database_size_mb']} MB")
                
        except Exception as e:
            print(f"⚠️ لا يمكن الحصول على إحصائيات قاعدة البيانات: {e}")
        
        # إنشاء نسخة احتياطية
        try:
            print("\n💾 إنشاء نسخة احتياطية...")
            if create_automatic_backup():
                print("✅ تم إنشاء النسخة الاحتياطية بنجاح")
            else:
                print("⚠️ فشل في إنشاء النسخة الاحتياطية")
        except Exception as e:
            print(f"⚠️ خطأ في النسخ الاحتياطي: {e}")
    
    # تشغيل التطبيق
    print("\n🌐 بدء تشغيل الخادم...")
    print("📱 يمكنك الوصول للنظام على: http://localhost:5000")
    print("🛑 اضغط Ctrl+C لإيقاف الخادم")
    
    try:
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        )
    except KeyboardInterrupt:
        print("\n👋 تم إيقاف الخادم")
    except Exception as e:
        logger.error(f"خطأ في تشغيل الخادم: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()