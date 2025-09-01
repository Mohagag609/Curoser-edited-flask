#!/usr/bin/env python3
"""إصلاح أخطاء قاعدة البيانات وإضافة الحقول المفقودة"""

from acc import create_app, db
from sqlalchemy import text
import sys

def fix_database():
    """إصلاح مشاكل قاعدة البيانات"""
    app = create_app()
    
    with app.app_context():
        print("🔧 بدء إصلاح قاعدة البيانات...")
        
        try:
            # 1. Clean up any hanging transactions
            print("1️⃣ تنظيف المعاملات المعلقة...")
            db.session.rollback()
            db.session.remove()
            
            # 2. Add missing columns to installments table
            print("2️⃣ إضافة الحقول المفقودة لجدول الأقساط...")
            
            # Check if columns exist before adding
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='installments'
            """))
            existing_columns = [row[0] for row in result]
            
            # Add project_id if missing
            if 'project_id' not in existing_columns:
                print("   - إضافة حقل project_id...")
                db.session.execute(text("""
                    ALTER TABLE installments 
                    ADD COLUMN project_id VARCHAR(20)
                """))
                db.session.commit()
            
            # Add contract_id if missing
            if 'contract_id' not in existing_columns:
                print("   - إضافة حقل contract_id...")
                db.session.execute(text("""
                    ALTER TABLE installments 
                    ADD COLUMN contract_id VARCHAR(20)
                """))
                db.session.commit()
            
            # Add customer_id if missing
            if 'customer_id' not in existing_columns:
                print("   - إضافة حقل customer_id...")
                db.session.execute(text("""
                    ALTER TABLE installments 
                    ADD COLUMN customer_id VARCHAR(20)
                """))
                db.session.commit()
            
            # 3. Update existing installments with missing data
            print("3️⃣ تحديث البيانات الموجودة...")
            
            # Get installments with missing project_id
            result = db.session.execute(text("""
                UPDATE installments 
                SET project_id = units.project_id 
                FROM units 
                WHERE installments.unit_id = units.id 
                AND installments.project_id IS NULL
            """))
            db.session.commit()
            print(f"   - تم تحديث {result.rowcount} سجل بـ project_id")
            
            # 4. Create indexes for better performance
            print("4️⃣ إنشاء الفهارس...")
            
            try:
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_installments_project_id 
                    ON installments(project_id)
                """))
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_installments_contract_id 
                    ON installments(contract_id)
                """))
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_installments_due_date 
                    ON installments(due_date)
                """))
                db.session.commit()
                print("   ✅ تم إنشاء الفهارس")
            except Exception as e:
                print(f"   ⚠️ تحذير في الفهارس: {str(e)}")
                db.session.rollback()
            
            # 5. Vacuum the database
            print("5️⃣ تحسين قاعدة البيانات...")
            try:
                db.session.execute(text("VACUUM ANALYZE"))
                print("   ✅ تم تحسين قاعدة البيانات")
            except:
                print("   ⚠️ لا يمكن تنفيذ VACUUM في معاملة")
            
            print("\n✅ تم إصلاح قاعدة البيانات بنجاح!")
            return True
            
        except Exception as e:
            print(f"\n❌ خطأ: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.session.remove()

if __name__ == '__main__':
    success = fix_database()
    sys.exit(0 if success else 1)