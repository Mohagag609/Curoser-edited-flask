#!/usr/bin/env python3
"""
إضافة unique constraints للنماذج
هذا سكريبت مؤقت لإضافة الفهارس الفريدة
"""
from acc import create_app
from acc.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # إضافة unique constraint للعملاء (name + phone)
        db.session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_name_phone 
            ON customers(name, phone) 
            WHERE phone IS NOT NULL
        """))
        print("✓ تم إضافة unique constraint للعملاء")
        
        # إضافة unique constraint للموردين (name)
        db.session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_suppliers_name 
            ON suppliers(name)
        """))
        print("✓ تم إضافة unique constraint للموردين")
        
        # إضافة unique constraint للشركاء (name)
        db.session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_partners_name 
            ON partners(name)
        """))
        print("✓ تم إضافة unique constraint للشركاء")
        
        # إضافة unique constraint للمقاولين (name)
        db.session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_contractors_name 
            ON contractors(name)
        """))
        print("✓ تم إضافة unique constraint للمقاولين")
        
        # إضافة unique constraint للوسطاء (name + phone)
        db.session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_brokers_name_phone 
            ON brokers(name, phone) 
            WHERE phone IS NOT NULL
        """))
        print("✓ تم إضافة unique constraint للوسطاء")
        
        # إضافة unique constraint للوحدات (unit_number + project_id)
        db.session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_units_number_project 
            ON units(unit_number, project_id)
        """))
        print("✓ تم إضافة unique constraint للوحدات")
        
        # إضافة unique constraint للمواد (name)
        db.session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_materials_name 
            ON materials(name)
        """))
        print("✓ تم إضافة unique constraint للمواد")
        
        # إضافة unique constraint للمشاريع (name)
        db.session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_name 
            ON projects(name)
        """))
        print("✓ تم إضافة unique constraint للمشاريع")
        
        db.session.commit()
        print("\n✅ تم إضافة جميع unique constraints بنجاح!")
        
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ خطأ: {str(e)}")