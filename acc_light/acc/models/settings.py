from acc.extensions import db
from sqlalchemy import Integer, Column, String, JSON, DateTime, func


class Settings(db.Model):
    __tablename__ = 'settings'
    
    key = Column(String(50), primary_key=True)
    value = Column(JSON)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<Settings {self.key}>'
    
    @staticmethod
    def get(key, default=None):
        setting = Settings.query.get(key)
        return setting.value if setting else default
    
    @staticmethod
    def set(key, value):
        setting = Settings.query.get(key)
        if setting:
            setting.value = value
        else:
            setting = Settings(key=key, value=value)
            db.session.add(setting)
        db.session.commit()