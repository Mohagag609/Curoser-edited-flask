"""
نظام Migrations منظم لإدارة قاعدة البيانات
"""
from flask_migrate import Migrate
from acc.extensions import db

migrate = Migrate()

def init_migrations(app):
    """تهيئة نظام migrations"""
    migrate.init_app(app, db)
    return migrate