#!/usr/bin/env python3
"""إصلاح سريع لمشاكل قاعدة البيانات"""

import os
import sys

# Set environment variable
os.environ['FLASK_APP'] = 'acc'
os.environ['FLASK_ENV'] = 'production'

from acc import create_app, db

def quick_fix():
    """إصلاح سريع للمشاكل"""
    app = create_app()
    
    with app.app_context():
        print("🔧 إصلاح سريع...")
        
        try:
            # 1. Rollback any pending transactions
            print("1️⃣ تنظيف المعاملات المعلقة...")
            db.session.rollback()
            db.session.remove()
            db.engine.dispose()
            
            # 2. Create new session
            print("2️⃣ إنشاء جلسة جديدة...")
            db.create_scoped_session()
            
            # 3. Test connection
            print("3️⃣ اختبار الاتصال...")
            result = db.session.execute("SELECT 1")
            print("   ✅ الاتصال يعمل")
            
            # 4. Check for missing columns
            print("4️⃣ التحقق من الأعمدة...")
            try:
                result = db.session.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'installments'
                """)
                columns = [row[0] for row in result]
                print(f"   أعمدة الأقساط: {columns}")
                
                # Add missing columns if needed
                if 'project_id' not in columns:
                    print("   ⚠️ إضافة project_id...")
                    db.session.execute("ALTER TABLE installments ADD COLUMN project_id VARCHAR(20)")
                    db.session.commit()
                    
                if 'contract_id' not in columns:
                    print("   ⚠️ إضافة contract_id...")
                    db.session.execute("ALTER TABLE installments ADD COLUMN contract_id VARCHAR(20)")
                    db.session.commit()
                    
                if 'customer_id' not in columns:
                    print("   ⚠️ إضافة customer_id...")
                    db.session.execute("ALTER TABLE installments ADD COLUMN customer_id VARCHAR(20)")
                    db.session.commit()
                    
            except Exception as e:
                print(f"   ⚠️ تحذير: {str(e)}")
                db.session.rollback()
            
            print("\n✅ تم الإصلاح!")
            return True
            
        except Exception as e:
            print(f"\n❌ خطأ: {str(e)}")
            return False
        finally:
            db.session.remove()

if __name__ == '__main__':
    success = quick_fix()
    sys.exit(0 if success else 1)