from datetime import datetime
from acc.extensions import db
from sqlalchemy import Column, String, Text, DateTime, func


class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False)
    national_id = Column(String(20))
    address = Column(Text)
    status = Column(String(20), default='نشط')
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    contracts = db.relationship('Contract', backref='customer', lazy='dynamic')
    
    def __repr__(self):
        return f'<Customer {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'national_id': self.national_id,
            'address': self.address,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }