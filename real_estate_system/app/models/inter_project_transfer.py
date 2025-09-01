from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Numeric, ForeignKey, Date, index
from sqlalchemy.orm import relationship


class InterProjectTransfer(BaseModel):
    """تحويل بين المشاريع"""
    __tablename__ = 'inter_project_transfers'
    
    from_project_id = Column(String(20), ForeignKey('projects.id'), nullable=False, index=True)
    to_project_id = Column(String(20), ForeignKey('projects.id'), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    transfer_date = Column(Date, nullable=False, index=True)
    description = Column(Text)
    reference = Column(String(100))
    status = Column(String(20), default='مكتمل', index=True)
    
    # Relationships
    from_project = relationship('Project', foreign_keys=[from_project_id], backref='transfers_from')
    to_project = relationship('Project', foreign_keys=[to_project_id], backref='transfers_to')
    
    def __repr__(self):
        return f'<InterProjectTransfer {self.from_project.name} -> {self.to_project.name} - {self.amount}>'
    
    @property
    def is_completed(self):
        """هل التحويل مكتمل؟"""
        return self.status == 'مكتمل'
    
    def to_dict(self):
        """تحويل التحويل إلى قاموس"""
        return {
            'id': self.id,
            'from_project_id': self.from_project_id,
            'to_project_id': self.to_project_id,
            'amount': float(self.amount) if self.amount else 0,
            'transfer_date': self.transfer_date.isoformat() if self.transfer_date else None,
            'description': self.description,
            'reference': self.reference,
            'status': self.status,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }