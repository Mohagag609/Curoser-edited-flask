"""
نظام إدارة قاعدة البيانات المبسط - متوافق مع PostgreSQL
"""
from acc.extensions import db
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class SimpleDatabaseManager:
    """مدير قاعدة البيانات المبسط"""
    
    def __init__(self, app=None):
        self.app = app
    
    def init_app(self, app):
        """تهيئة مدير قاعدة البيانات"""
        self.app = app
    
    def create_essential_indexes(self):
        """إنشاء الفهارس الأساسية فقط"""
        with self.app.app_context():
            try:
                # فهارس أساسية فقط
                essential_indexes = [
                    # فهارس العملاء
                    "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)",
                    "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
                    
                    # فهارس المشاريع
                    "CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name)",
                    "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
                    
                    # فهارس الوحدات
                    "CREATE INDEX IF NOT EXISTS idx_units_project_id ON units(project_id)",
                    "CREATE INDEX IF NOT EXISTS idx_units_status ON units(status)",
                    
                    # فهارس العقود
                    "CREATE INDEX IF NOT EXISTS idx_contracts_project_id ON contracts(project_id)",
                    "CREATE INDEX IF NOT EXISTS idx_contracts_customer_id ON contracts(customer_id)",
                    "CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status)",
                    
                    # فهارس الأقساط
                    "CREATE INDEX IF NOT EXISTS idx_installments_project_id ON installments(project_id)",
                    "CREATE INDEX IF NOT EXISTS idx_installments_unit_id ON installments(unit_id)",
                    "CREATE INDEX IF NOT EXISTS idx_installments_due_date ON installments(due_date)",
                    "CREATE INDEX IF NOT EXISTS idx_installments_status ON installments(status)",
                    
                    # فهارس السندات
                    "CREATE INDEX IF NOT EXISTS idx_vouchers_project_id ON vouchers(project_id)",
                    "CREATE INDEX IF NOT EXISTS idx_vouchers_type ON vouchers(type)",
                    "CREATE INDEX IF NOT EXISTS idx_vouchers_date ON vouchers(date)",
                ]
                
                success_count = 0
                for index in essential_indexes:
                    try:
                        db.session.execute(text(index))
                        db.session.commit()
                        success_count += 1
                        logger.debug(f"✅ Created index: {index.split(' ')[5]}")
                    except Exception as e:
                        db.session.rollback()
                        logger.warning(f"⚠️ Index warning: {e}")
                
                logger.info(f"✅ Created {success_count}/{len(essential_indexes)} essential indexes")
                return True
                
            except Exception as e:
                logger.error(f"❌ Error creating indexes: {str(e)}")
                return False
    
    def optimize_database(self):
        """تحسين قاعدة البيانات"""
        with self.app.app_context():
            try:
                # تحسين إعدادات PostgreSQL
                if 'postgresql' in db.engine.url.drivername:
                    optimizations = [
                        "ANALYZE",  # تحليل الإحصائيات
                    ]
                    
                    for optimization in optimizations:
                        try:
                            db.session.execute(text(optimization))
                            db.session.commit()
                            logger.debug(f"✅ PostgreSQL optimization: {optimization}")
                        except Exception as e:
                            db.session.rollback()
                            logger.warning(f"⚠️ Optimization warning: {e}")
                
                logger.info("✅ Database optimization completed")
                return True
                
            except Exception as e:
                logger.error(f"❌ Database optimization failed: {str(e)}")
                return False
    
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
            
            return stats

# مثيل عام لمدير قاعدة البيانات المبسط
simple_database_manager = SimpleDatabaseManager()

def init_simple_database(app):
    """تهيئة قاعدة البيانات المبسطة"""
    manager = SimpleDatabaseManager(app)
    return manager

def create_essential_indexes(app):
    """إنشاء الفهارس الأساسية"""
    manager = SimpleDatabaseManager(app)
    return manager.create_essential_indexes()

def optimize_database_simple(app):
    """تحسين قاعدة البيانات المبسط"""
    manager = SimpleDatabaseManager(app)
    return manager.optimize_database()

def get_database_stats_simple(app):
    """الحصول على إحصائيات قاعدة البيانات"""
    manager = SimpleDatabaseManager(app)
    return manager.get_database_stats()