from acc.extensions import db
from sqlalchemy import Column, String, Float, Numeric, Text, DateTime, func, ForeignKey


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
    
    def get_total_partners_percentage(self):
        """Calculate total percentage of all partners"""
        return sum(up.percentage for up in self.partners)
    
    @property 
    def contracts(self):
        from acc.models import Contract
        return Contract.query.filter_by(unit_id=self.id).first()
    
    @property
    def installments(self):
        from acc.models import Installment
        return Installment.query.filter_by(unit_id=self.id).all()
    
    def calculate_remaining(self):
        """Calculate remaining amount to be paid for this unit"""
        contract = self.contracts
        if not contract:
            return 0
        
        total_owed = (contract.total_price or 0) - (contract.discount_amount or 0)
        
        # Get all vouchers related to this unit
        from acc.models.voucher import Voucher
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