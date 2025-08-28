import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'acc_light.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Pagination
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 20))
    
    # Application settings
    SITE_NAME = 'نظام إدارة العقارات'
    DEFAULT_LOCALE = 'ar'