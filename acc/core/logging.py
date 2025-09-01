"""
نظام Logging منظم ومتقدم
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

class LoggingManager:
    """مدير نظام Logging"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """تهيئة نظام Logging"""
        self.app = app
        
        # إنشاء مجلد السجلات
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        # إعداد مستوى السجلات
        log_level = logging.DEBUG if app.debug else logging.INFO
        app.logger.setLevel(log_level)
        
        # إزالة المعالجات الافتراضية
        for handler in app.logger.handlers[:]:
            app.logger.removeHandler(handler)
        
        # معالج ملف السجلات مع التدوير
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/acc.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # معالج ملف الأخطاء
        error_handler = logging.handlers.RotatingFileHandler(
            'logs/errors.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # معالج وحدة التحكم
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # تنسيق السجلات
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # إضافة المعالجات
        app.logger.addHandler(file_handler)
        app.logger.addHandler(error_handler)
        app.logger.addHandler(console_handler)
        
        # منع تكرار السجلات
        app.logger.propagate = False
        
        # تسجيل بدء التطبيق
        app.logger.info('🚀 ACC Application started')
        
        return app.logger

def get_logger(name: str = None):
    """الحصول على logger"""
    return logging.getLogger(name or __name__)

def log_action(action: str, user_id: str = None, details: str = None):
    """تسجيل العمليات"""
    logger = get_logger('actions')
    message = f"Action: {action}"
    if user_id:
        message += f" | User: {user_id}"
    if details:
        message += f" | Details: {details}"
    logger.info(message)

def log_error(error: Exception, context: str = None):
    """تسجيل الأخطاء"""
    logger = get_logger('errors')
    message = f"Error: {str(error)}"
    if context:
        message += f" | Context: {context}"
    logger.error(message, exc_info=True)

def log_performance(operation: str, duration: float, details: str = None):
    """تسجيل الأداء"""
    logger = get_logger('performance')
    message = f"Operation: {operation} | Duration: {duration:.3f}s"
    if details:
        message += f" | Details: {details}"
    logger.info(message)