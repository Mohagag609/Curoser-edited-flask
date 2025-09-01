from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Numeric, ForeignKey, Date, index
from sqlalchemy.orm import relationship


class Installment(BaseModel):
    """نموذج القسط"""
    __tablename__ = 'installments'
    
    contract_id = Column(String(20), ForeignKey('contracts.id'), nullable=False, index=True)
    installment_number = Column(String(20), nullable=False)  # رقم القسط
    amount = Column(Numeric(15, 2), nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    payment_date = Column(Date, index=True)
    status = Column(String(50), default='معلق', index=True)  # معلق، مدفوع، متأخر
    payment_method = Column(String(50))  # نقدي، شيك، تحويل
    payment_reference = Column(String(100))  # رقم الشيك أو التحويل
    notes = Column(Text)
    
    # Relationships
    contract = relationship('Contract', backref='installment_contracts')
    
    def __repr__(self):
        return f'<Installment {self.installment_number} - {self.contract.code}>'
    
    @property
    def is_paid(self):
        """هل القسط مدفوع؟"""
        return self.status == 'مدفوع'
    
    @property
    def is_pending(self):
        """هل القسط معلق؟"""
        return self.status == 'معلق'
    
    @property
    def is_overdue(self):
        """هل القسط متأخر؟"""
        from datetime import date
        return self.status == 'معلق' and self.due_date < date.today()
    
    @property
    def days_overdue(self):
        """عدد الأيام المتأخرة"""
        from datetime import date
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0
    
    def mark_as_paid(self, payment_date=None, payment_method=None, payment_reference=None, notes=None):
        """تسجيل القسط كمدفوع"""
        from datetime import date
        self.status = 'مدفوع'
        self.payment_date = payment_date or date.today()
        self.payment_method = payment_method
        self.payment_reference = payment_reference
        self.notes = notes
        self.save()
    
    def mark_as_pending(self):
        """تسجيل القسط كمعلق"""
        self.status = 'معلق'
        self.payment_date = None
        self.payment_method = None
        self.payment_reference = None
        self.save()
    
    def update_status(self):
        """تحديث حالة القسط"""
        from datetime import date
        if self.status == 'معلق' and self.due_date < date.today():
            self.status = 'متأخر'
            self.save()
    
    def to_dict(self):
        """تحويل القسط إلى قاموس"""
        return {
            'id': self.id,
            'contract_id': self.contract_id,
            'installment_number': self.installment_number,
            'amount': float(self.amount) if self.amount else 0,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
            'notes': self.notes,
            'is_paid': self.is_paid,
            'is_pending': self.is_pending,
            'is_overdue': self.is_overdue,
            'days_overdue': self.days_overdue,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }