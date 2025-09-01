from app import db
from sqlalchemy import Column, String, DateTime, func
from datetime import datetime


class BaseModel(db.Model):
    """نموذج أساسي يحتوي على الحقول المشتركة"""
    __abstract__ = True
    
    id = Column(String(20), primary_key=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    
    def to_dict(self):
        """تحويل النموذج إلى قاموس"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def save(self):
        """حفظ النموذج في قاعدة البيانات"""
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    def delete(self):
        """حذف النموذج من قاعدة البيانات"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def get_by_id(cls, id):
        """الحصول على نموذج بالمعرف"""
        return cls.query.get(id)
    
    @classmethod
    def get_all(cls):
        """الحصول على جميع النماذج"""
        return cls.query.all()
    
    @classmethod
    def get_active(cls):
        """الحصول على النماذج النشطة فقط"""
        if hasattr(cls, 'status'):
            return cls.query.filter_by(status='نشط').all()
        return cls.get_all()