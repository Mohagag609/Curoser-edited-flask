from acc.extensions import db
from sqlalchemy import Integer, Column, String, Float, Numeric, Text, DateTime, func, ForeignKey


class Unit(db.Model):
    __tablename__ = 'units'
    
    id = Column(String(20), primary_key=True)
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=True)  # nullable for backward compatibility
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    floor = Column(String(20), nullable=False)
    building = Column(String(50), nullable=False)
    area = Column(Float)
    unit_type = Column(String(50), default='سكني')
    total_price = Column(Numeric(15, 2), nullable=False)
    status = Column(String(20), default='متاحة')
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    partners = db.relationship('UnitPartner', backref='unit', lazy='dynamic', cascade='all, delete-orphan')
    debts = db.relationship('PartnerDebt', backref='unit', lazy='dynamic')
    # contracts and installments relationships are handled by Contract and Installment models via backref
    
    def __repr__(self):
        return f'<Unit {self.code}>'
    
    def get_display_name(self):
        """Returns display name similar to original app"""
        parts = []
        if self.name:
            parts.append(self.name)
        if self.building:
            parts.append(self.building)
        if self.floor:
            parts.append(f"الدور {self.floor}")
        return ' - '.join(parts) if parts else self.code
    
    def get_full_name(self):
        """Returns full unit name for display in table"""
        parts = []
        if self.name:
            parts.append(self.name)
        if self.floor:
            parts.append(f"الدور {self.floor}")
        if self.building:
            parts.append(f"عمارة {self.building}")
        return ' '.join(parts) if parts else self.code
    
    def get_total_partners_percentage(self):
        """Calculate total percentage of all partners"""
        return sum(up.percentage for up in self.partners)
    
    def calculate_remaining(self):
        """Calculate remaining amount to be paid for this unit"""
        # Handle both query and list cases
        if hasattr(self.contracts, 'first'):
            # It's a query
            contract = self.contracts.first()
        else:
            # It's a list
            contract = self.contracts[0] if len(self.contracts) > 0 else None
            
        if not contract:
            return 0
        
        total_owed = (contract.total_price or 0) - (contract.discount_amount or 0)
        
        # Get all vouchers related to this unit
        from acc.models.voucher import Voucher
        
        # Handle installments as list or query
        if hasattr(self.installments, 'all'):
            installment_ids = [i.id for i in self.installments.all()]
        else:
            installment_ids = [i.id for i in self.installments]
        
        # Build query for vouchers
        voucher_query = db.session.query(func.sum(Voucher.amount)).filter(
            Voucher.type == 'receipt'
        )
        
        # Add conditions based on what references exist
        if installment_ids:
            voucher_query = voucher_query.filter(
                db.or_(
                    Voucher.linked_ref == contract.id,
                    Voucher.linked_ref.in_(installment_ids)
                )
            )
        else:
            voucher_query = voucher_query.filter(Voucher.linked_ref == contract.id)
        
        total_paid = voucher_query.scalar() or 0
        
        remaining = total_owed - total_paid
        return max(0, remaining)