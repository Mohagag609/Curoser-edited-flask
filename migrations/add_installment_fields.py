"""إضافة حقول جديدة لجدول الأقساط

هذا السكريبت يضيف الحقول المطلوبة لربط الأقساط بالعقود والعملاء والمشاريع
"""

from acc import create_app, db
from sqlalchemy import text

def upgrade():
    """إضافة الحقول الجديدة"""
    app = create_app()
    
    with app.app_context():
        try:
            # إضافة حقل project_id
            db.session.execute(text("""
                ALTER TABLE installments 
                ADD COLUMN IF NOT EXISTS project_id VARCHAR(20) 
                REFERENCES projects(id)
            """))
            
            # إضافة حقل contract_id  
            db.session.execute(text("""
                ALTER TABLE installments 
                ADD COLUMN IF NOT EXISTS contract_id VARCHAR(20) 
                REFERENCES contracts(id)
            """))
            
            # إضافة حقل customer_id
            db.session.execute(text("""
                ALTER TABLE installments 
                ADD COLUMN IF NOT EXISTS customer_id VARCHAR(20) 
                REFERENCES customers(id)
            """))
            
            # تغيير اسم payment_date إلى paid_date إذا كان موجود
            db.session.execute(text("""
                DO $$ 
                BEGIN
                    IF EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='installments' AND column_name='payment_date') THEN
                        ALTER TABLE installments RENAME COLUMN payment_date TO paid_date;
                    END IF;
                END $$;
            """))
            
            db.session.commit()
            print("✅ تم إضافة الحقول الجديدة بنجاح")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ خطأ: {str(e)}")

if __name__ == '__main__':
    upgrade()