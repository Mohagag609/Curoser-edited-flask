from acc.extensions import db
from sqlalchemy import Column, String, Text, JSON, DateTime, func


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = Column(String(20), primary_key=True)
    timestamp = Column(DateTime, default=func.now())
    description = Column(Text)
    details = Column(JSON)
    user_id = Column(String(20))  # للمستقبل
    ip_address = Column(String(45))  # للمستقبل
    
    def __repr__(self):
        return f'<AuditLog {self.timestamp} - {self.description}>'