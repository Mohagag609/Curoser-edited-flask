"""
نظام إدارة قاعدة البيانات المحسن
"""
from acc.extensions import db
from sqlalchemy import text, Index
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """مدير قاعدة البيانات"""
    
    def __init__(self, app=None):
        self.app = app
    
    def init_app(self, app):
        """تهيئة مدير قاعدة البيانات"""
        self.app = app
    
    def create_all_indexes(self):
        """إنشاء جميع الفهارس"""
        with self.app.app_context():
            try:
                # فهارس العملاء
                self._create_customer_indexes()
                
                # فهارس المشاريع
                self._create_project_indexes()
                
                # فهارس الوحدات
                self._create_unit_indexes()
                
                # فهارس العقود
                self._create_contract_indexes()
                
                # فهارس الأقساط
                self._create_installment_indexes()
                
                # فهارس السندات
                self._create_voucher_indexes()
                
                # فهارس الشركاء
                self._create_partner_indexes()
                
                # فهارس الخزائن
                self._create_safe_indexes()
                
                # فهارس مركبة للبحث السريع
                self._create_composite_indexes()
                
                logger.info("✅ تم إنشاء جميع الفهارس بنجاح")
                return True
                
            except Exception as e:
                logger.error(f"❌ خطأ في إنشاء الفهارس: {str(e)}")
                return False
    
    def _create_customer_indexes(self):
        """إنشاء فهارس العملاء"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)",
            "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
            "CREATE INDEX IF NOT EXISTS idx_customers_national_id ON customers(national_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(code)",
            "CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status)",
            "CREATE INDEX IF NOT EXISTS idx_customers_project_id ON customers(project_id)",
        ]
        
        for index in indexes:
            try:
                db.session.execute(text(index))
                db.session.commit()
                logger.debug(f"✅ Created customer index: {index.split(' ')[5]}")
            except Exception as e:
                db.session.rollback()
                logger.warning(f"⚠️ Customer index warning: {e}")
    
    def _create_project_indexes(self):
        """إنشاء فهارس المشاريع"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)",
            "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
            "CREATE INDEX IF NOT EXISTS idx_projects_code ON projects(code)",
        ]
        
        for index in indexes:
            try:
                db.session.execute(text(index))
                logger.debug(f"✅ Created project index: {index.split(' ')[5]}")
            except Exception as e:
                logger.warning(f"⚠️ Project index warning: {e}")
    
    def _create_unit_indexes(self):
        """إنشاء فهارس الوحدات"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_units_project_id ON units(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_units_status ON units(status)",
            "CREATE INDEX IF NOT EXISTS idx_units_code ON units(code)",
            "CREATE INDEX IF NOT EXISTS idx_units_type ON units(type)",
            "CREATE INDEX IF NOT EXISTS idx_units_floor ON units(floor)",
        ]
        
        for index in indexes:
            try:
                db.session.execute(text(index))
                logger.debug(f"✅ Created unit index: {index.split(' ')[5]}")
            except Exception as e:
                logger.warning(f"⚠️ Unit index warning: {e}")
    
    def _create_contract_indexes(self):
        """إنشاء فهارس العقود"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_contracts_project_id ON contracts(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_customer_id ON contracts(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_unit_id ON contracts(unit_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_code ON contracts(code)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_payment_type ON contracts(payment_type)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_start_date ON contracts(start_date)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_is_active ON contracts(is_active)",
        ]
        
        for index in indexes:
            try:
                db.session.execute(text(index))
                logger.debug(f"✅ Created contract index: {index.split(' ')[5]}")
            except Exception as e:
                logger.warning(f"⚠️ Contract index warning: {e}")
    
    def _create_installment_indexes(self):
        """إنشاء فهارس الأقساط"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_installments_project_id ON installments(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_installments_contract_id ON installments(contract_id)",
            "CREATE INDEX IF NOT EXISTS idx_installments_unit_id ON installments(unit_id)",
            "CREATE INDEX IF NOT EXISTS idx_installments_customer_id ON installments(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_installments_due_date ON installments(due_date)",
            "CREATE INDEX IF NOT EXISTS idx_installments_status ON installments(status)",
            "CREATE INDEX IF NOT EXISTS idx_installments_is_overdue ON installments(is_overdue)",
            "CREATE INDEX IF NOT EXISTS idx_installments_type ON installments(type)",
        ]
        
        for index in indexes:
            try:
                db.session.execute(text(index))
                db.session.commit()  # Commit after each index
                logger.debug(f"✅ Created installment index: {index.split(' ')[5]}")
            except Exception as e:
                db.session.rollback()  # Rollback on error
                logger.warning(f"⚠️ Installment index warning: {e}")
    
    def _create_voucher_indexes(self):
        """إنشاء فهارس السندات"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_vouchers_project_id ON vouchers(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_safe_id ON vouchers(safe_id)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_type ON vouchers(type)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_date ON vouchers(date)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_status ON vouchers(status)",
        ]
        
        for index in indexes:
            try:
                db.session.execute(text(index))
                logger.debug(f"✅ Created voucher index: {index.split(' ')[5]}")
            except Exception as e:
                logger.warning(f"⚠️ Voucher index warning: {e}")
    
    def _create_partner_indexes(self):
        """إنشاء فهارس الشركاء"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_partners_name ON partners(name)",
            "CREATE INDEX IF NOT EXISTS idx_partners_phone ON partners(phone)",
            "CREATE INDEX IF NOT EXISTS idx_partners_status ON partners(status)",
            "CREATE INDEX IF NOT EXISTS idx_partners_type ON partners(type)",
        ]
        
        for index in indexes:
            try:
                db.session.execute(text(index))
                logger.debug(f"✅ Created partner index: {index.split(' ')[5]}")
            except Exception as e:
                logger.warning(f"⚠️ Partner index warning: {e}")
    
    def _create_safe_indexes(self):
        """إنشاء فهارس الخزائن"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_safes_name ON safes(name)",
            "CREATE INDEX IF NOT EXISTS idx_safes_type ON safes(type)",
            "CREATE INDEX IF NOT EXISTS idx_safes_status ON safes(status)",
        ]
        
        for index in indexes:
            try:
                db.session.execute(text(index))
                logger.debug(f"✅ Created safe index: {index.split(' ')[5]}")
            except Exception as e:
                logger.warning(f"⚠️ Safe index warning: {e}")
    
    def _create_composite_indexes(self):
        """إنشاء الفهارس المركبة للبحث السريع"""
        indexes = [
            # فهارس مركبة للعقود
            "CREATE INDEX IF NOT EXISTS idx_contracts_project_customer ON contracts(project_id, customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_project_status ON contracts(project_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_contracts_customer_status ON contracts(customer_id, status)",
            
            # فهارس مركبة للأقساط
            "CREATE INDEX IF NOT EXISTS idx_installments_unit_status ON installments(unit_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_installments_project_due_date ON installments(project_id, due_date)",
            "CREATE INDEX IF NOT EXISTS idx_installments_customer_status ON installments(customer_id, status)",
            
            # فهارس مركبة للسندات
            "CREATE INDEX IF NOT EXISTS idx_vouchers_project_date ON vouchers(project_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_vouchers_safe_type ON vouchers(safe_id, type)",
            
            # فهارس مركبة للوحدات
            "CREATE INDEX IF NOT EXISTS idx_units_project_status ON units(project_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_units_project_type ON units(project_id, type)",
        ]
        
        for index in indexes:
            try:
                db.session.execute(text(index))
                logger.debug(f"✅ Created composite index: {index.split(' ')[5]}")
            except Exception as e:
                logger.warning(f"⚠️ Composite index warning: {e}")
    
    def optimize_database(self):
        """تحسين قاعدة البيانات"""
        with self.app.app_context():
            try:
                # تحسين إعدادات SQLite
                if 'sqlite' in db.engine.url.drivername:
                    self._optimize_sqlite()
                
                # تنظيف قاعدة البيانات
                self._vacuum_database()
                
                logger.info("✅ تم تحسين قاعدة البيانات بنجاح")
                return True
                
            except Exception as e:
                logger.error(f"❌ خطأ في تحسين قاعدة البيانات: {str(e)}")
                return False
    
    def _optimize_sqlite(self):
        """تحسين إعدادات SQLite"""
        optimizations = [
            "PRAGMA journal_mode = WAL",
            "PRAGMA synchronous = NORMAL",
            "PRAGMA cache_size = -64000",  # 64MB cache
            "PRAGMA temp_store = MEMORY",
            "PRAGMA mmap_size = 268435456",  # 256MB memory-mapped I/O
            "PRAGMA optimize",
        ]
        
        for optimization in optimizations:
            try:
                db.session.execute(text(optimization))
                logger.debug(f"✅ SQLite optimization: {optimization}")
            except Exception as e:
                logger.warning(f"⚠️ SQLite optimization warning: {e}")
    
    def _vacuum_database(self):
        """تنظيف وضغط قاعدة البيانات"""
        try:
            db.session.execute(text("VACUUM ANALYZE"))
            logger.info("✅ Database vacuumed and analyzed")
        except Exception as e:
            logger.warning(f"⚠️ Vacuum warning: {e}")
    
    def get_database_stats(self):
        """إحصائيات قاعدة البيانات"""
        with self.app.app_context():
            stats = {}
            
            # إحصائيات الجداول
            tables = [
                'customers', 'projects', 'units', 'contracts', 
                'installments', 'vouchers', 'partners', 'safes'
            ]
            
            for table in tables:
                try:
                    result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    stats[table] = count
                except Exception as e:
                    logger.warning(f"Could not get count for {table}: {e}")
                    stats[table] = 0
            
            # حجم قاعدة البيانات
            try:
                if 'sqlite' in db.engine.url.drivername:
                    result = db.session.execute(text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"))
                    size = result.scalar()
                    stats['database_size_bytes'] = size
                    stats['database_size_mb'] = round(size / (1024 * 1024), 2)
            except Exception as e:
                logger.warning(f"Could not get database size: {e}")
            
            return stats

# مثيل عام لمدير قاعدة البيانات
database_manager = DatabaseManager()

def init_database(app):
    """تهيئة قاعدة البيانات"""
    manager = DatabaseManager(app)
    return manager

def create_all_indexes(app):
    """إنشاء جميع الفهارس"""
    manager = DatabaseManager(app)
    return manager.create_all_indexes()

def optimize_database(app):
    """تحسين قاعدة البيانات"""
    manager = DatabaseManager(app)
    return manager.optimize_database()

def get_database_stats(app):
    """الحصول على إحصائيات قاعدة البيانات"""
    manager = DatabaseManager(app)
    return manager.get_database_stats()