from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Text, Boolean, index


class Settings(BaseModel):
    """إعدادات النظام"""
    __tablename__ = 'settings'
    
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    description = Column(Text)
    category = Column(String(50), index=True)
    is_public = Column(Boolean, default=False)
    
    def __repr__(self):
        return f'<Settings {self.key}>'
    
    @classmethod
    def get_setting(cls, key, default=None):
        """الحصول على إعداد"""
        setting = cls.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @classmethod
    def set_setting(cls, key, value, description=None, category=None, is_public=False):
        """تعيين إعداد"""
        setting = cls.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.description = description
            setting.category = category
            setting.is_public = is_public
        else:
            setting = cls(
                key=key,
                value=value,
                description=description,
                category=category,
                is_public=is_public
            )
        setting.save()
        return setting
    
    @classmethod
    def get_public_settings(cls):
        """الحصول على الإعدادات العامة"""
        return cls.query.filter_by(is_public=True).all()
    
    def to_dict(self):
        """تحويل الإعداد إلى قاموس"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'category': self.category,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }