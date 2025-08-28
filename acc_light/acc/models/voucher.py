from acc.extensions import db
from sqlalchemy import Column, String, Numeric, ForeignKey, Date, Text, DateTime, func


class Voucher(db.Model):
    __tablename__ = 'vouchers'
    
    id = Column(String(20), primary_key=True)
    type = Column(String(20), nullable=False)  # 'receipt' or 'payment'
    date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    safe_id = Column(String(20), ForeignKey('safes.id'), nullable=False)
    description = Column(Text)
    payer = Column(String(200))  # للقبض
    beneficiary = Column(String(200))  # للصرف
    linked_ref = Column(String(20))  # contract_id, installment_id, etc.
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f'<Voucher {self.type} - {self.amount}>'