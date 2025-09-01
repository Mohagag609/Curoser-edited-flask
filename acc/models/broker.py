from acc.extensions import db
from sqlalchemy import Integer, Column, String, Numeric, ForeignKey, DateTime, func


class Broker(db.Model):
    __tablename__ = 'brokers'
    
    id = Column(String(20), primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False, unique=True)
    phone = Column(String(20))
    national_id = Column(String(20), unique=True)
    commission_percentage = Column(Numeric(5, 2), default=0)
    address = Column(db.Text)
    status = Column(String(20), default='نشط')
    notes = Column(db.Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f'<Broker {self.name}>'


class BrokerDue(db.Model):
    __tablename__ = 'broker_dues'
    
    id = Column(String(20), primary_key=True)
    contract_id = Column(String(20), ForeignKey('contracts.id'), nullable=False)
    broker_name = Column(String(200))
    amount = Column(Numeric(15, 2), nullable=False)
    due_date = Column(db.Date)
    status = Column(String(20), default='due')
    payment_date = Column(db.Date)
    paid_from_safe_id = Column(String(20), ForeignKey('safes.id'))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    contract = db.relationship('Contract', backref='broker_dues')
    safe = db.relationship('Safe', backref='broker_payments')