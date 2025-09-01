"""
ملف الإعدادات الرئيسي - تم تحديثه لاستخدام النظام الجديد
"""
import os
from dotenv import load_dotenv
from acc.core.config import config as core_config

# تحميل متغيرات البيئة
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# استخدام النظام الجديد للإعدادات
Config = core_config[os.environ.get('FLASK_ENV', 'default')]

# إعدادات إضافية خاصة بالتطبيق
Config.SITE_NAME = 'نظام إدارة العقارات'
Config.DEFAULT_LOCALE = 'ar'
Config.ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 20))

# إصلاح URL قاعدة البيانات لـ Render
if hasattr(Config, 'SQLALCHEMY_DATABASE_URI'):
    db_url = Config.SQLALCHEMY_DATABASE_URI
    if db_url.startswith('postgres://'):
        Config.SQLALCHEMY_DATABASE_URI = db_url.replace('postgres://', 'postgresql://', 1)