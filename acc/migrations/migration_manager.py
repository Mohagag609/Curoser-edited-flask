"""
مدير Migrations مخصص لإدارة قاعدة البيانات
"""
from acc import create_app
from acc.extensions import db
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class MigrationManager:
    """مدير Migrations مخصص"""
    
    def __init__(self):
        self.app = create_app()
        
    def run_migrations(self):
        """تشغيل جميع migrations"""
        with self.app.app_context():
            try:
                # 1. إضافة الحقول المفقودة
                self._add_missing_columns()
                
                # 2. إنشاء الفهارس
                self._create_indexes()
                
                # 3. تحسين إعدادات SQLite
                self._optimize_sqlite_settings()
                
                # 4. تنظيف قاعدة البيانات
                self._vacuum_database()
                
                logger.info("✅ تم تشغيل جميع migrations بنجاح")
                return True
                
            except Exception as e:
                logger.error(f"❌ خطأ في migrations: {str(e)}")
                db.session.rollback()
                return False
            finally:
                db.session.remove()
    
    def _add_missing_columns(self):
        """إضافة الحقول المفقودة"""
        logger.info("🔧 إضافة الحقول المفقودة...")
        
        # فحص وإضافة الحقول المفقودة لجدول الأقساط
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='installments'
        """))
        existing_columns = [row[0] for row in result]
        
        missing_columns = [
            ('project_id', 'VARCHAR(20)'),
            ('contract_id', 'VARCHAR(20)'),
            ('customer_id', 'VARCHAR(20)')
        ]
        
        for column_name, column_type in missing_columns:
            if column_name not in existing_columns:
                logger.info(f"   - إضافة حقل {column_name}...")
                db.session.execute(text(f"""
                    ALTER TABLE installments 
                    ADD COLUMN {column_name} {column_type}
                """))
                db.session.commit()
        
        # تحديث البيانات الموجودة
        self._update_existing_data()
    
    def _update_existing_data(self):
        """تحديث البيانات الموجودة"""
        logger.info("🔄 تحديث البيانات الموجودة...")
        
        # تحديث project_id للأقساط
        result = db.session.execute(text("""
            UPDATE installments 
            SET project_id = units.project_id 
            FROM units 
            WHERE installments.unit_id = units.id 
            AND installments.project_id IS NULL
        """))
        db.session.commit()
        logger.info(f"   - تم تحديث {result.rowcount} سجل بـ project_id")
    
    def _create_indexes(self):
        """إنشاء الفهارس"""
        logger.info("📊 إنشاء الفهارس...")
        
        indexes = [
            # فهارس العملاء
            "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)",
            "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
            "CREATE INDEX IF NOT EXISTS idx_customers_national_id ON customers(national_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(code)",
            
            # فهارس المشاريع
            "CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)",
            "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
            
            # فهارس الوحدات
            "CREATE INDEX IF NOT EXISTS idx_units_project_id ON units(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_units_status ON units(status)",
            "CREATE INDEX IF NOT EXISTS idx_units_code ON units(code)",
            
            # فهارس العقود
            "CREATE INDEX IF NOT EXISTS idx_contracts_project_id ON contracts(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_customer_id ON contracts(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_unit_id ON contracts(unit_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status)",
            
            # فهارس السندات
            "CREATE INDEX IF NOT EXISTS idx_vouchers_project_id ON vouchers(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_safe_id ON vouchers(safe_id)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_type ON vouchers(type)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_date ON vouchers(date)",
            
            # فهارس الأقساط
            "CREATE INDEX IF NOT EXISTS idx_installments_unit_id ON installments(unit_id)",
            "CREATE INDEX IF NOT EXISTS idx_installments_project_id ON installments(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_installments_contract_id ON installments(contract_id)",
            "CREATE INDEX IF NOT EXISTS idx_installments_due_date ON installments(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_installments_status ON installments(status)",
            
            # فهارس مركبة للبحث السريع
            "CREATE INDEX IF NOT EXISTS idx_contracts_project_customer ON contracts(project_id, customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_project_status ON contracts(project_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_project_date ON vouchers(project_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_installments_unit_status ON installments(unit_id, status)",
        ]
        
        for index in indexes:
            try:
                db.session.execute(text(index))
                logger.info(f"   ✅ {index.split(' ')[5]}")
            except Exception as e:
                logger.warning(f"   ⚠️ {index.split(' ')[5]}: {e}")
        
        db.session.commit()
    
    def _optimize_sqlite_settings(self):
        """تحسين إعدادات SQLite"""
        if 'sqlite' not in db.engine.url.drivername:
            logger.info("⏭️ تخطي تحسينات SQLite (استخدام PostgreSQL)")
            return
            
        logger.info("⚙️ تحسين إعدادات SQLite...")
        
        optimizations = [
            "PRAGMA journal_mode = WAL",
            "PRAGMA synchronous = NORMAL", 
            "PRAGMA cache_size = -64000",
            "PRAGMA temp_store = MEMORY",
            "PRAGMA mmap_size = 268435456",
        ]
        
        for optimization in optimizations:
            try:
                db.session.execute(text(optimization))
                logger.info(f"   ✅ {optimization}")
            except Exception as e:
                logger.warning(f"   ⚠️ {optimization}: {e}")
    
    def _vacuum_database(self):
        """تنظيف وضغط قاعدة البيانات"""
        logger.info("🧹 تنظيف قاعدة البيانات...")
        try:
            db.session.execute(text("VACUUM ANALYZE"))
            logger.info("   ✅ تم تنظيف قاعدة البيانات")
        except Exception as e:
            logger.warning(f"   ⚠️ لا يمكن تنفيذ VACUUM: {e}")

def run_migrations():
    """تشغيل migrations"""
    manager = MigrationManager()
    return manager.run_migrations()

if __name__ == "__main__":
    success = run_migrations()
    exit(0 if success else 1)