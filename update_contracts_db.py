#!/usr/bin/env python3
"""
تحديث قاعدة البيانات لاستخدام نماذج العقود والأقساط المحسّنة
"""

import os
import sys
from datetime import datetime

# إعداد البيئة
# إعداد البيئة
if not os.environ.get('FLASK_APP'):
    os.environ['FLASK_APP'] = 'app'
if not os.environ.get('FLASK_ENV'):
    os.environ['FLASK_ENV'] = 'development'

# إضافة المسار الحالي
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔧 تحديث قاعدة البيانات للنماذج المحسّنة...\n")

try:
    from acc import create_app, db
    from sqlalchemy import text, inspect
    
    app = create_app()
    
    with app.app_context():
        print("1️⃣ فحص الجداول الحالية...")
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        print(f"   الجداول الموجودة: {', '.join(existing_tables)}")
        
        print("\n2️⃣ إضافة الأعمدة الجديدة للعقود...")
        
        # قائمة الأعمدة الجديدة للعقود
        contract_columns = [
            ("unit_price", "NUMERIC(15,2)"),
            ("discount_percent", "NUMERIC(5,2) DEFAULT 0"),
            ("final_price", "NUMERIC(15,2)"),
            ("down_payment_percent", "NUMERIC(5,2) DEFAULT 0"),
            ("broker_id", "VARCHAR(20)"),
            ("commission_paid", "BOOLEAN DEFAULT FALSE"),
            ("commission_payment_date", "DATE"),
            ("installment_amount", "NUMERIC(15,2) DEFAULT 0"),
            ("extra_annual_payments", "INTEGER DEFAULT 0"),
            ("contract_date", "DATE"),
            ("end_date", "DATE"),
            ("delivery_date", "DATE"),
            ("notes", "TEXT"),
            ("terms_conditions", "TEXT"),
            ("created_by", "VARCHAR(20)"),
            ("approved_by", "VARCHAR(20)"),
            ("approval_date", "DATETIME")
        ]
        
        # فحص وإضافة الأعمدة
        if 'contracts' in existing_tables:
            try:
            existing_columns = [col['name'] for col in inspector.get_columns('contracts')]
        except:
            existing_columns = []
            
            for column_name, column_type in contract_columns:
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE contracts ADD COLUMN {column_name} {column_type}"
                        db.session.execute(text(sql))
                        print(f"   ✅ تم إضافة عمود {column_name}")
                    except Exception as e:
                        if "duplicate column" not in str(e).lower():
                            print(f"   ⚠️ فشل إضافة عمود {column_name}: {str(e)}")
        
        print("\n3️⃣ إضافة الأعمدة الجديدة للأقساط...")
        
        # قائمة الأعمدة الجديدة للأقساط
        installment_columns = [
            ("paid_amount", "NUMERIC(15,2) DEFAULT 0"),
            ("penalty_amount", "NUMERIC(15,2) DEFAULT 0"),
            ("discount_amount", "NUMERIC(15,2) DEFAULT 0"),
            ("grace_period_days", "INTEGER DEFAULT 0"),
            ("payment_method", "VARCHAR(50)"),
            ("payment_reference", "VARCHAR(100)"),
            ("collected_by", "VARCHAR(20)"),
            ("notes", "TEXT")
        ]
        
        # فحص وإضافة الأعمدة
        if 'installments' in existing_tables:
            existing_columns = [col['name'] for col in inspector.get_columns('installments')]
            
            for column_name, column_type in installment_columns:
                if column_name not in existing_columns:
                    try:
                        sql = f"ALTER TABLE installments ADD COLUMN {column_name} {column_type}"
                        db.session.execute(text(sql))
                        print(f"   ✅ تم إضافة عمود {column_name}")
                    except Exception as e:
                        if "duplicate column" not in str(e).lower():
                            print(f"   ⚠️ فشل إضافة عمود {column_name}: {str(e)}")
        
        print("\n4️⃣ إنشاء الجداول الجديدة...")
        
        # جدول وثائق العقود
        if 'contract_documents' not in existing_tables:
            create_documents_table = """
            CREATE TABLE contract_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_id VARCHAR(20) NOT NULL,
                document_type VARCHAR(50) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_name VARCHAR(200) NOT NULL,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                uploaded_by VARCHAR(20),
                FOREIGN KEY (contract_id) REFERENCES contracts (id)
            )
            """
            db.session.execute(text(create_documents_table))
            print("   ✅ تم إنشاء جدول contract_documents")
        
        # جدول دفعات الأقساط
        if 'installment_payments' not in existing_tables:
            create_payments_table = """
            CREATE TABLE installment_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                installment_id VARCHAR(20) NOT NULL,
                amount NUMERIC(15,2) NOT NULL,
                payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                payment_method VARCHAR(50),
                reference VARCHAR(100),
                notes TEXT,
                created_by VARCHAR(20),
                FOREIGN KEY (installment_id) REFERENCES installments (id)
            )
            """
            db.session.execute(text(create_payments_table))
            print("   ✅ تم إنشاء جدول installment_payments")
        
        # جدول تذكيرات الأقساط
        if 'installment_reminders' not in existing_tables:
            create_reminders_table = """
            CREATE TABLE installment_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                installment_id VARCHAR(20) NOT NULL,
                sent_date DATE NOT NULL,
                method VARCHAR(50),
                status VARCHAR(50),
                response TEXT,
                FOREIGN KEY (installment_id) REFERENCES installments (id)
            )
            """
            db.session.execute(text(create_reminders_table))
            print("   ✅ تم إنشاء جدول installment_reminders")
        
        print("\n5️⃣ تحديث البيانات الموجودة...")
        
        # تحديث العقود الموجودة
        try:
            # إضافة unit_price من total_price للعقود الموجودة
            db.session.execute(text("""
                UPDATE contracts 
                SET unit_price = total_price,
                    final_price = total_price,
                    contract_date = start_date
                WHERE unit_price IS NULL
            """))
            
            # تحديث paid_amount للأقساط من الفرق بين original_amount و amount
            db.session.execute(text("""
                UPDATE installments 
                SET paid_amount = CASE 
                    WHEN original_amount IS NOT NULL 
                    THEN original_amount - amount 
                    ELSE 0 
                END
                WHERE paid_amount IS NULL OR paid_amount = 0
            """))
            
            print("   ✅ تم تحديث البيانات الموجودة")
        except Exception as e:
            print(f"   ⚠️ خطأ في تحديث البيانات: {str(e)}")
        
        # حفظ التغييرات
        db.session.commit()
        
        print("\n6️⃣ إنشاء الفهارس لتحسين الأداء...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_contracts_project ON contracts(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_customer ON contracts(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_unit ON contracts(unit_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status)",
            "CREATE INDEX IF NOT EXISTS idx_installments_contract ON installments(contract_id)",
            "CREATE INDEX IF NOT EXISTS idx_installments_due_date ON installments(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_installments_status ON installments(status)"
        ]
        
        for index_sql in indexes:
            try:
                db.session.execute(text(index_sql))
                print(f"   ✅ {index_sql.split()[-1]}")
            except Exception as e:
                print(f"   ⚠️ {index_sql.split()[-1]}: {str(e)}")
        
        db.session.commit()
        
        print("\n✅ تم تحديث قاعدة البيانات بنجاح!")
        
        # إحصائيات
        contract_count = db.session.execute(text("SELECT COUNT(*) FROM contracts")).scalar()
        installment_count = db.session.execute(text("SELECT COUNT(*) FROM installments")).scalar()
        
        print(f"\n📊 الإحصائيات:")
        print(f"   - عدد العقود: {contract_count}")
        print(f"   - عدد الأقساط: {installment_count}")
        
except Exception as e:
    print(f"\n❌ خطأ: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n📋 الخطوات التالية:")
print("1. تحديث ملفات النماذج لاستخدام النماذج المحسّنة")
print("2. تحديث ملفات routes لاستخدام routes_enhanced.py")
print("3. اختبار النظام بالكامل")
print("4. نقل البيانات القديمة إلى النظام الجديد إذا لزم الأمر")