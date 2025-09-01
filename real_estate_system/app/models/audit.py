from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Text, index


class AuditLog(BaseModel):
    """سجل التدقيق"""
    __tablename__ = 'audit_logs'
    
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(20), nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)  # CREATE, UPDATE, DELETE
    old_values = Column(Text)
    new_values = Column(Text)
    user_id = Column(String(20), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    def __repr__(self):
        return f'<AuditLog {self.table_name}.{self.record_id} - {self.action}>'
    
    def to_dict(self):
        """تحويل سجل التدقيق إلى قاموس"""
        return {
            'id': self.id,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'action': self.action,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }