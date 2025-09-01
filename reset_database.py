#!/usr/bin/env python3
"""
سكريبت مسح قاعدة البيانات وإنشائها نظيفة
"""
import os
import sys
from acc import create_app
from acc.extensions import db

def reset_database():
    """مسح قاعدة البيانات وإنشائها نظيفة"""
    print("🗑️ مسح قاعدة البيانات...")
    
    # إنشاء التطبيق
    app = create_app()
    
    with app.app_context():
        try:
            # حذف جميع الجداول
            print("1️⃣ حذف جميع الجداول...")
            db.drop_all()
            print("   ✅ تم حذف جميع الجداول")
            
            # إنشاء جميع الجداول من جديد
            print("2️⃣ إنشاء الجداول من جديد...")
            db.create_all()
            print("   ✅ تم إنشاء جميع الجداول")
            
            # إنشاء البيانات الأساسية
            print("3️⃣ إنشاء البيانات الأساسية...")
            create_basic_data()
            print("   ✅ تم إنشاء البيانات الأساسية")
            
            print("\n🎉 تم إعادة تعيين قاعدة البيانات بنجاح!")
            return True
            
        except Exception as e:
            print(f"\n❌ خطأ في إعادة تعيين قاعدة البيانات: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.session.remove()

def create_basic_data():
    """إنشاء البيانات الأساسية"""
    from acc.models import Project, Safe, Settings
    from acc.services.code_generator import generate_project_code, generate_safe_code
    
    # إنشاء مشروع افتراضي
    default_project = Project(
        id=generate_project_code(),
        name='مشروع افتراضي',
        code='DEFAULT',
        description='المشروع الافتراضي للنظام',
        project_type='عقاري',
        status='نشط',
        is_default=True
    )
    db.session.add(default_project)
    
    # إنشاء خزينة افتراضية
    default_safe = Safe(
        id=generate_safe_code(),
        name='الخزينة الرئيسية',
        type='رئيسية',
        project_id=default_project.id,
        status='نشط'
    )
    db.session.add(default_safe)
    
    # إنشاء إعدادات النظام
    settings = Settings(
        key='system_name',
        value='نظام إدارة العقارات',
        description='اسم النظام'
    )
    db.session.add(settings)
    
    db.session.commit()
    print(f"   - مشروع افتراضي: {default_project.name}")
    print(f"   - خزينة افتراضية: {default_safe.name}")
    print(f"   - إعدادات النظام: {settings.value}")

def main():
    """تشغيل إعادة تعيين قاعدة البيانات"""
    print("⚠️ تحذير: هذا سيمسح جميع البيانات الموجودة!")
    response = input("هل أنت متأكد؟ (اكتب 'yes' للمتابعة): ")
    
    if response.lower() != 'yes':
        print("❌ تم إلغاء العملية")
        return
    
    success = reset_database()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()