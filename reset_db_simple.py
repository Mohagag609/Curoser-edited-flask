#!/usr/bin/env python3
"""
سكريبت مبسط لمسح قاعدة البيانات في Render
"""
import os
from acc import create_app
from acc.extensions import db

def reset_database():
    """مسح قاعدة البيانات وإنشائها نظيفة"""
    print("🗑️ Resetting database...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # حذف جميع الجداول
            print("Dropping all tables...")
            db.drop_all()
            print("✅ All tables dropped")
            
            # إنشاء جميع الجداول من جديد
            print("Creating all tables...")
            db.create_all()
            print("✅ All tables created")
            
            # إنشاء البيانات الأساسية
            print("Creating basic data...")
            create_basic_data()
            print("✅ Basic data created")
            
            print("🎉 Database reset completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Database reset failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def create_basic_data():
    """إنشاء البيانات الأساسية"""
    from acc.models import Project, Safe
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
    
    db.session.commit()
    print(f"   - Default project: {default_project.name}")
    print(f"   - Default safe: {default_safe.name}")

if __name__ == '__main__':
    reset_database()