from acc.extensions import db
from sqlalchemy import Integer, Column, String, Numeric, ForeignKey, Date, DateTime, func


class Installment(db.Model):
    __tablename__ = 'installments'
    
    id = Column(String(20), primary_key=True)
    unit_id = Column(String(20), ForeignKey('units.id'), nullable=False)
    installment_number = Column(db.Integer)
    
    # Relationships
    unit = db.relationship('Unit', backref='installments')
    type = Column(String(50))  # شهري/ربع سنوي/دفعة سنوية/دفعة صيانة
    original_amount = Column(Numeric(15, 2))
    amount = Column(Numeric(15, 2), nullable=False)  # المتبقي
    due_date = Column(Date)
    payment_date = Column(Date)
    status = Column(String(20), default='غير مدفوع')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f'<Installment {self.id} - {self.amount}>'
    
    def get_paid_amount(self):
        """Calculate the paid amount"""
        original = self.original_amount if self.original_amount else self.amount
        return original - self.amount