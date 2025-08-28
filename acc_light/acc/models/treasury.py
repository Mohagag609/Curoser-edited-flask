from acc.extensions import db
from sqlalchemy import Column, String, Numeric, DateTime, func, Boolean

class Safe(db.Model):
    __tablename__ = 'safes'
    
    id = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    type = Column(String(20), default='cash')  # cash / bank
    balance = Column(Numeric(15, 2), default=0)
    bank_name = Column(String(200))
    account_number = Column(String(50))
    is_default = Column(Boolean, default=False)
    notes = Column(db.Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    vouchers = db.relationship('Voucher', backref='safe', lazy='dynamic')
    transfers_from = db.relationship('SafeTransfer', foreign_keys='SafeTransfer.from_safe_id', backref='from_safe', lazy='dynamic')
    transfers_to = db.relationship('SafeTransfer', foreign_keys='SafeTransfer.to_safe_id', backref='to_safe', lazy='dynamic')
    
    def __repr__(self):
        return f'<Safe {self.name}>'
    
    def update_balance(self):
        """Update safe balance based on vouchers"""
        from acc.models import Voucher
        from sqlalchemy import func
        
        # Calculate receipts
        receipts = db.session.query(func.sum(Voucher.amount)).filter(
            Voucher.safe_id == self.id,
            Voucher.type == 'receipt'
        ).scalar() or 0
        
        # Calculate payments
        payments = db.session.query(func.sum(Voucher.amount)).filter(
            Voucher.safe_id == self.id,
            Voucher.type == 'payment'
        ).scalar() or 0
        
        # Calculate transfers in
        transfers_in = db.session.query(func.sum(SafeTransfer.amount)).filter(
            SafeTransfer.to_safe_id == self.id
        ).scalar() or 0
        
        # Calculate transfers out
        transfers_out = db.session.query(func.sum(SafeTransfer.amount)).filter(
            SafeTransfer.from_safe_id == self.id
        ).scalar() or 0
        
        self.balance = receipts - payments + transfers_in - transfers_out
        
        return self.balance


class SafeTransfer(db.Model):
    __tablename__ = 'safe_transfers'
    
    id = Column(String(20), primary_key=True)
    from_safe_id = Column(String(20), db.ForeignKey('safes.id'), nullable=False)
    to_safe_id = Column(String(20), db.ForeignKey('safes.id'), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    date = Column(DateTime, default=func.now())
    description = Column(String(500))
    notes = Column(db.Text)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f'<SafeTransfer {self.id}>'