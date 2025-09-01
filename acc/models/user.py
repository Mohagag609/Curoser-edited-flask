from acc.extensions import db
from sqlalchemy import Column, String, Boolean, DateTime, func

class User(db.Model):
    """نموذج المستخدمين البسيط"""
    __tablename__ = 'users'
    __table_args__ = {"extend_existing": True}
    
    id = Column(String(20), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    role = Column(String(20), default='user')  # user, admin, manager
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<User {self.username}>'
