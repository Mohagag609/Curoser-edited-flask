#!/usr/bin/env python3
"""
تحسينات قاعدة البيانات
إضافة indexes وتحسينات للأداء
"""
from acc import create_app
from acc.extensions import db
from sqlalchemy import text

def add_database_indexes():
    """إضافة indexes لتحسين سرعة البحث"""
    app = create_app()
    
    with app.app_context():
        indexes = [
            # Customers indexes
            "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)",
            "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
            "CREATE INDEX IF NOT EXISTS idx_customers_national_id ON customers(national_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(code)",
            
            # Projects indexes
            "CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)",
            "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
            
            # Units indexes
            "CREATE INDEX IF NOT EXISTS idx_units_project_id ON units(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_units_status ON units(status)",
            "CREATE INDEX IF NOT EXISTS idx_units_code ON units(code)",
            
            # Contracts indexes
            "CREATE INDEX IF NOT EXISTS idx_contracts_project_id ON contracts(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_customer_id ON contracts(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_unit_id ON contracts(unit_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status)",
            
            # Vouchers indexes
            "CREATE INDEX IF NOT EXISTS idx_vouchers_project_id ON vouchers(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_safe_id ON vouchers(safe_id)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_type ON vouchers(type)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_date ON vouchers(date)",
            
            # Installments indexes
            "CREATE INDEX IF NOT EXISTS idx_installments_contract_id ON installments(contract_id)",
            "CREATE INDEX IF NOT EXISTS idx_installments_due_date ON installments(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_installments_status ON installments(status)",
        ]
        
        print("🔧 Adding database indexes...")
        
        with db.engine.connect() as conn:
            for index in indexes:
                try:
                    conn.execute(text(index))
                    print(f"✅ {index.split(' ')[5]}")
                except Exception as e:
                    print(f"⚠️ {index.split(' ')[5]}: {e}")
            conn.commit()
        
        print("\n✅ Database optimization completed!")

def optimize_sqlite_settings():
    """تحسين إعدادات SQLite"""
    app = create_app()
    
    with app.app_context():
        optimizations = [
            "PRAGMA journal_mode = WAL",  # Write-Ahead Logging للأداء
            "PRAGMA synchronous = NORMAL",  # توازن بين الأداء والأمان
            "PRAGMA cache_size = -64000",  # 64MB cache
            "PRAGMA temp_store = MEMORY",  # استخدام الذاكرة للملفات المؤقتة
            "PRAGMA mmap_size = 268435456",  # 256MB memory-mapped I/O
        ]
        
        print("⚙️ Optimizing SQLite settings...")
        
        with db.engine.connect() as conn:
            for optimization in optimizations:
                try:
                    conn.execute(text(optimization))
                    print(f"✅ {optimization}")
                except Exception as e:
                    print(f"⚠️ {optimization}: {e}")
        
        print("\n✅ SQLite optimization completed!")

if __name__ == "__main__":
    print("🚀 Starting database optimizations...\n")
    add_database_indexes()
    print()
    optimize_sqlite_settings()
    print("\n🎉 All optimizations completed!")