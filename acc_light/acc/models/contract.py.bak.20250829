from acc.extensions import db
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, Date, DateTime, func


class Contract(db.Model):
    __tablename__ = 'contracts'
    
    id = Column(String(20), primary_key=True)
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=True)  # nullable for backward compatibility
    code = Column(String(20), unique=True)
    unit_id = Column(String(20), ForeignKey('units.id'), nullable=False)
    customer_id = Column(String(20), ForeignKey('customers.id'), nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)
    down_payment = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    maintenance_deposit = Column(Numeric(15, 2), default=0)
    broker_name = Column(String(200))
    broker_percent = Column(Numeric(5, 2), default=0)
    broker_amount = Column(Numeric(15, 2), default=0)
    commission_safe_id = Column(String(20), ForeignKey('safes.id'))
    payment_type = Column(String(20))  # 'cash' or 'installment'
    installment_type = Column(String(20))  # شهري/ربع سنوي/نصف سنوي/سنوي
    installment_count = Column(Integer, default=0)
    extra_annual = Column(Integer, default=0)
    annual_payment_value = Column(Numeric(15, 2), default=0)
    start_date = Column(Date, nullable=False)
    status = Column(String(20), default='نشط')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    commission_safe = db.relationship('Safe', backref='contracts')
    customer = db.relationship('Customer', foreign_keys=[customer_id], backref='contracts')
    unit = db.relationship('Unit', foreign_keys=[unit_id], backref='contracts')
    installments = db.relationship('Installment', 
                                 primaryjoin="Contract.unit_id==Installment.unit_id",
                                 foreign_keys=[unit_id],
                                 viewonly=True)
    
    def __repr__(self):
        return f'<Contract {self.code}>'