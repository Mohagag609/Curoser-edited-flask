from acc.extensions import db
from sqlalchemy import Integer, Column, String, Numeric, ForeignKey, Date, Text, DateTime, func


class Voucher(db.Model):
    __tablename__ = 'vouchers'
    
    id = Column(String(20), primary_key=True)
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=True)  # nullable for backward compatibility
    type = Column(String(20), nullable=False)  # 'receipt' or 'payment'
    date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    safe_id = Column(String(20), ForeignKey('safes.id'), nullable=False)
    entity_type = Column(String(20))  # customer, supplier, contractor, partner
    entity_id = Column(String(20))
    description = Column(Text)
    payer = Column(String(200))  # للقبض
    beneficiary = Column(String(200))  # للصرف
    linked_ref = Column(String(20))  # contract_id, installment_id, etc.
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f'<Voucher {self.type} - {self.amount}>'
    
    def get_entity(self):
        """Get the associated entity object"""
        if not self.entity_type or not self.entity_id:
            return None
        
        if self.entity_type == 'customer':
            from acc.models import Customer
            return Customer.query.get(self.entity_id)
        elif self.entity_type == 'supplier':
            from acc.models import Supplier
            return Supplier.query.get(self.entity_id)
        elif self.entity_type == 'contractor':
            from acc.models import Contractor
            return Contractor.query.get(self.entity_id)
        elif self.entity_type == 'partner':
            from acc.models import Partner
            return Partner.query.get(self.entity_id)
        
        return None