#!/usr/bin/env python3
"""
تحسينات الأداء الفورية
Quick Performance Improvements
"""
from functools import lru_cache
import json
from datetime import datetime, timedelta

# 1. إضافة In-Memory Caching
class SimpleCache:
    """Cache بسيط في الذاكرة"""
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
        self.timeout = 300  # 5 دقائق
    
    def get(self, key):
        if key in self.cache:
            if datetime.now() - self.timestamps[key] < timedelta(seconds=self.timeout):
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key, value, timeout=None):
        self.cache[key] = value
        self.timestamps[key] = datetime.now()
        return value
    
    def clear(self):
        self.cache.clear()
        self.timestamps.clear()

# 2. Query Optimization Helpers
def optimize_customer_query(filters=None):
    """استعلام محسّن للعملاء"""
    from acc.models import Customer
    from acc.extensions import db
    
    # اختيار الحقول المطلوبة فقط
    query = db.session.query(
        Customer.id,
        Customer.code,
        Customer.name,
        Customer.phone,
        Customer.status
    )
    
    if filters:
        if 'search' in filters:
            search = f"%{filters['search']}%"
            query = query.filter(
                db.or_(
                    Customer.name.like(search),
                    Customer.phone.like(search),
                    Customer.code.like(search)
                )
            )
        if 'status' in filters:
            query = query.filter(Customer.status == filters['status'])
    
    return query.all()

# 3. Batch Operations
def bulk_update_installments_status():
    """تحديث حالة الأقساط دفعة واحدة"""
    from acc.models import Installment
    from acc.extensions import db
    from datetime import date
    
    # تحديث الأقساط المتأخرة
    db.session.execute(
        """
        UPDATE installments 
        SET status = 'متأخر' 
        WHERE due_date < :today 
        AND status = 'مستحق'
        AND paid_amount < amount
        """,
        {'today': date.today()}
    )
    db.session.commit()

# 4. Dashboard Stats Caching
@lru_cache(maxsize=32)
def get_dashboard_stats_cached(project_id, cache_key):
    """إحصائيات لوحة التحكم مع cache"""
    from acc.models import Contract, Unit, Voucher, Customer
    from acc.extensions import db
    from sqlalchemy import func
    
    stats = {}
    
    # إحصائيات بـ single query
    contract_stats = db.session.query(
        func.count(Contract.id).label('total'),
        func.sum(Contract.total_price).label('total_value'),
        Contract.status
    ).filter_by(project_id=project_id).group_by(Contract.status).all()
    
    stats['contracts'] = {
        'total': sum(s.total for s in contract_stats),
        'total_value': sum(s.total_value or 0 for s in contract_stats),
        'by_status': {s.status: s.total for s in contract_stats}
    }
    
    # وحدات
    unit_stats = db.session.query(
        func.count(Unit.id).label('total'),
        Unit.status
    ).filter_by(project_id=project_id).group_by(Unit.status).all()
    
    stats['units'] = {
        'total': sum(s.total for s in unit_stats),
        'by_status': {s.status: s.total for s in unit_stats}
    }
    
    # إيرادات ومصروفات
    finance_stats = db.session.query(
        func.sum(Voucher.amount).label('total'),
        Voucher.type
    ).filter_by(project_id=project_id).group_by(Voucher.type).all()
    
    stats['finance'] = {
        'income': next((s.total for s in finance_stats if s.type == 'قبض'), 0) or 0,
        'expense': next((s.total for s in finance_stats if s.type == 'صرف'), 0) or 0
    }
    
    # عملاء
    stats['customers'] = db.session.query(func.count(Customer.id)).scalar() or 0
    
    return stats

# 5. Connection Pool Monitoring
def check_db_connections():
    """فحص اتصالات قاعدة البيانات"""
    from acc import create_app
    from acc.extensions import db
    
    app = create_app()
    with app.app_context():
        pool = db.engine.pool
        print(f"🔌 Database Connection Pool Status:")
        print(f"   Size: {pool.size()}")
        print(f"   Checked out: {pool.checked_out_connections}")
        print(f"   Overflow: {pool.overflow()}")
        print(f"   Total: {pool.size() + pool.overflow()}")

# 6. Vacuum Database (تنظيف وضغط)
def vacuum_database():
    """تنظيف وضغط قاعدة البيانات"""
    from acc import create_app
    from acc.extensions import db
    
    app = create_app()
    with app.app_context():
        print("🧹 Vacuuming database...")
        db.session.execute("VACUUM")
        db.session.execute("ANALYZE")
        print("✅ Database vacuumed and analyzed!")

# 7. إضافة Indexes إضافية للبحث
def add_search_indexes():
    """إضافة indexes للبحث السريع"""
    from acc import create_app
    from acc.extensions import db
    from sqlalchemy import text
    
    app = create_app()
    with app.app_context():
        extra_indexes = [
            # Composite indexes للبحث المركب
            "CREATE INDEX IF NOT EXISTS idx_contracts_project_customer ON contracts(project_id, customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_project_status ON contracts(project_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_project_date ON vouchers(project_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_installments_contract_status ON installments(contract_id, status)",
            
            # Partial indexes للقيم الشائعة
            "CREATE INDEX IF NOT EXISTS idx_units_available ON units(project_id) WHERE status = 'متاحة'",
            "CREATE INDEX IF NOT EXISTS idx_contracts_active ON contracts(project_id) WHERE status = 'نشط'",
            "CREATE INDEX IF NOT EXISTS idx_installments_unpaid ON installments(contract_id) WHERE paid_amount < amount",
        ]
        
        print("🔧 Adding extra search indexes...")
        for index in extra_indexes:
            try:
                db.session.execute(text(index))
                print(f"✅ {index.split(' ')[5]}")
            except Exception as e:
                print(f"⚠️ {index.split(' ')[5]}: {e}")
        
        db.session.commit()
        print("✅ Extra indexes added!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "vacuum":
            vacuum_database()
        elif command == "indexes":
            add_search_indexes()
        elif command == "connections":
            check_db_connections()
        elif command == "all":
            print("🚀 Running all optimizations...\n")
            vacuum_database()
            print()
            add_search_indexes()
            print()
            check_db_connections()
        else:
            print("Usage: python performance_boost.py [vacuum|indexes|connections|all]")
    else:
        print("Performance optimization tools ready!")
        print("Run with: vacuum, indexes, connections, or all")