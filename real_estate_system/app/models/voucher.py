from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Numeric, ForeignKey, Date, index
from sqlalchemy.orm import relationship


class Voucher(BaseModel):
    """نموذج السند"""
    __tablename__ = 'vouchers'
    
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=True, index=True)
    safe_id = Column(String(20), ForeignKey('safes.id'), nullable=False, index=True)
    voucher_number = Column(String(50), unique=True, nullable=False, index=True)
    voucher_type = Column(String(20), nullable=False, index=True)  # إيراد، مصروف
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text)
    reference = Column(String(100))  # رقم المرجع
    voucher_date = Column(Date, nullable=False, index=True)
    status = Column(String(20), default='مكتمل', index=True)
    notes = Column(Text)
    
    # Relationships
    project = relationship('Project', backref='voucher_projects')
    safe = relationship('Safe', backref='voucher_safes')
    
    def __repr__(self):
        return f'<Voucher {self.voucher_number} - {self.voucher_type}>'
    
    @property
    def is_income(self):
        """هل السند إيراد؟"""
        return self.voucher_type == 'إيراد'
    
    @property
    def is_expense(self):
        """هل السند مصروف؟"""
        return self.voucher_type == 'مصروف'
    
    @property
    def is_completed(self):
        """هل السند مكتمل؟"""
        return self.status == 'مكتمل'
    
    def to_dict(self):
        """تحويل السند إلى قاموس"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'safe_id': self.safe_id,
            'voucher_number': self.voucher_number,
            'voucher_type': self.voucher_type,
            'amount': float(self.amount) if self.amount else 0,
            'description': self.description,
            'reference': self.reference,
            'voucher_date': self.voucher_date.isoformat() if self.voucher_date else None,
            'status': self.status,
            'notes': self.notes,
            'is_income': self.is_income,
            'is_expense': self.is_expense,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }