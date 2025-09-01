#!/usr/bin/env python3
"""
اختبار النظام المحسن
"""
import os
import sys
from acc import create_app
from acc.core.database import get_database_stats
from acc.core.backup import backup_manager
from acc.core.performance import performance_manager
from acc.core.logging import get_logger

logger = get_logger(__name__)

def test_system():
    """اختبار النظام المحسن"""
    print("🧪 اختبار النظام المحسن...")
    
    # إنشاء التطبيق
    app = create_app()
    
    with app.app_context():
        # اختبار قاعدة البيانات
        print("\n1️⃣ اختبار قاعدة البيانات...")
        try:
            stats = get_database_stats(app)
            print("✅ قاعدة البيانات تعمل بشكل صحيح")
            print(f"   إجمالي الجداول: {len([k for k in stats.keys() if not k.startswith('database_')])}")
            print(f"   حجم قاعدة البيانات: {stats.get('database_size_mb', 0)} MB")
        except Exception as e:
            print(f"❌ خطأ في قاعدة البيانات: {e}")
            return False
        
        # اختبار النسخ الاحتياطي
        print("\n2️⃣ اختبار النسخ الاحتياطي...")
        try:
            backups = backup_manager.list_backups()
            print(f"✅ نظام النسخ الاحتياطي يعمل ({len(backups)} نسخة)")
            if backups:
                latest = backups[0]
                print(f"   آخر نسخة: {latest['filename']} ({latest['size_mb']} MB)")
        except Exception as e:
            print(f"❌ خطأ في النسخ الاحتياطي: {e}")
            return False
        
        # اختبار الأداء
        print("\n3️⃣ اختبار نظام الأداء...")
        try:
            cache_stats = performance_manager.get_cache_stats()
            print(f"✅ نظام الأداء يعمل ({cache_stats['total_entries']} إدخال في التخزين المؤقت)")
        except Exception as e:
            print(f"❌ خطأ في نظام الأداء: {e}")
            return False
        
        # اختبار النماذج
        print("\n4️⃣ اختبار النماذج...")
        try:
            from acc.models import Customer, Contract, Installment, Project
            
            # اختبار العد
            customer_count = Customer.query.count()
            contract_count = Contract.query.count()
            installment_count = Installment.query.count()
            project_count = Project.query.count()
            
            print(f"✅ النماذج تعمل بشكل صحيح")
            print(f"   العملاء: {customer_count}")
            print(f"   العقود: {contract_count}")
            print(f"   الأقساط: {installment_count}")
            print(f"   المشاريع: {project_count}")
            
        except Exception as e:
            print(f"❌ خطأ في النماذج: {e}")
            return False
        
        # اختبار الخدمات
        print("\n5️⃣ اختبار الخدمات...")
        try:
            from acc.core.services import customer_service, contract_service, installment_service
            
            # اختبار إحصائيات العملاء
            customer_stats = customer_service.get_customer_stats()
            print(f"✅ الخدمات تعمل بشكل صحيح")
            print(f"   إحصائيات العملاء: {customer_stats['total']} عميل")
            
        except Exception as e:
            print(f"❌ خطأ في الخدمات: {e}")
            return False
        
        print("\n🎉 جميع الاختبارات نجحت!")
        print("✅ النظام المحسن جاهز للاستخدام")
        return True

def main():
    """تشغيل الاختبارات"""
    try:
        success = test_system()
        if success:
            print("\n🚀 يمكنك الآن تشغيل النظام بـ: python run_optimized.py")
            sys.exit(0)
        else:
            print("\n❌ فشل في الاختبارات")
            sys.exit(1)
    except Exception as e:
        logger.error(f"خطأ في الاختبار: {e}")
        print(f"\n❌ خطأ عام: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()