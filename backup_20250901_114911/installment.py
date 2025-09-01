from acc.extensions import db
from sqlalchemy import Integer, Column, String, Numeric, ForeignKey, Date, DateTime, func


class Installment(db.Model):
    __tablename__ = 'installments'
    
    id = Column(String(20), primary_key=True)
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False)
    contract_id = Column(String(20), ForeignKey('contracts.id'))
    unit_id = Column(String(20), ForeignKey('units.id'), nullable=False)
    customer_id = Column(String(20), ForeignKey('customers.id'))
    installment_number = Column(db.Integer)
    
    # Relationships
    project = db.relationship('Project', backref='installments')
    contract = db.relationship('Contract', foreign_keys=[contract_id])
    unit = db.relationship('Unit', backref='installments')
    customer = db.relationship('Customer', foreign_keys=[customer_id])
    type = Column(String(50))  # شهري/ربع سنوي/دفعة سنوية/دفعة صيانة
    original_amount = Column(Numeric(15, 2))
    amount = Column(Numeric(15, 2), nullable=False)  # المتبقي
    due_date = Column(Date)
    paid_date = Column(Date)
    status = Column(String(20), default='غير مدفوع')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f'<Installment {self.id} - {self.amount}>'
    
    def get_paid_amount(self):
        """Calculate the paid amount"""
        original = self.original_amount if self.original_amount else self.amount
        return original - self.amount