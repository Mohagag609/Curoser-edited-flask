from acc.extensions import db
from sqlalchemy import Integer, Column, String, Numeric, ForeignKey, Date, Text, DateTime, func


class Safe(db.Model):
    __tablename__ = 'safes'
    
    id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    balance = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    vouchers = db.relationship('Voucher', backref='safe', lazy='dynamic')
    transfers_from = db.relationship('Transfer', foreign_keys='Transfer.from_safe_id', 
                                     backref='from_safe', lazy='dynamic')
    transfers_to = db.relationship('Transfer', foreign_keys='Transfer.to_safe_id', 
                                   backref='to_safe', lazy='dynamic')
    
    def __repr__(self):
        return f'<Safe {self.name}>'


class Transfer(db.Model):
    __tablename__ = 'transfers'
    
    id = Column(String(20), primary_key=True)
    from_safe_id = Column(String(20), ForeignKey('safes.id'), nullable=False)
    to_safe_id = Column(String(20), ForeignKey('safes.id'), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    date = Column(Date, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())