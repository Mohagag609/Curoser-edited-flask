"""
نظام إعدادات موحد ومتقدم
"""
import os
from datetime import timedelta

class Config:
    """الإعدادات الأساسية"""
    
    # إعدادات Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # إعدادات قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///acc_light.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'check_same_thread': False,  # للـ SQLite
            'timeout': 20
        }
    }
    
    # إعدادات Caching
    CACHE_TYPE = 'simple'  # أو 'redis' للإنتاج
    CACHE_DEFAULT_TIMEOUT = 300  # 5 دقائق
    
    # إعدادات الجلسة
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # إعدادات الأمان
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # ساعة واحدة
    
    # إعدادات الملفات
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'xls'}
    
    # إعدادات النسخ الاحتياطي
    BACKUP_DIR = 'backups'
    MAX_BACKUPS = 30
    BACKUP_INTERVAL_HOURS = 24
    
    # إعدادات الأداء
    PAGINATION_PER_PAGE = 20
    SEARCH_RESULTS_LIMIT = 100
    
    # إعدادات التقارير
    REPORTS_DIR = 'reports'
    EXCEL_TEMPLATES_DIR = 'templates/excel'
    
    # إعدادات الإشعارات
    NOTIFICATIONS_ENABLED = True
    SMS_ENABLED = False
    EMAIL_ENABLED = False
    
    # إعدادات التطوير
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """إعدادات التطوير"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///acc_dev.db'

class ProductionConfig(Config):
    """إعدادات الإنتاج"""
    DEBUG = False
    CACHE_TYPE = 'redis'
    # إعدادات إضافية للإنتاج
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }

class TestingConfig(Config):
    """إعدادات الاختبار"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# قاموس الإعدادات
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}