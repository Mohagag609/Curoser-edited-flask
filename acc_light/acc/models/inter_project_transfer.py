from acc.extensions import db
from sqlalchemy import Column, String, Numeric, ForeignKey, Text, DateTime, func
from acc.services.utils import generate_uid


class InterProjectTransfer(db.Model):
    """نموذج تحويل الأموال بين المشاريع"""
    __tablename__ = 'inter_project_transfers'
    
    id = Column(String(20), primary_key=True, default=lambda: generate_uid('IPT'))
    
    # المشروع والخزينة المُرسلة
    from_project_id = Column(String(20), ForeignKey('projects.id'), nullable=False)
    from_safe_id = Column(String(20), ForeignKey('safes.id'), nullable=False)
    
    # المشروع والخزينة المُستقبلة
    to_project_id = Column(String(20), ForeignKey('projects.id'), nullable=False)
    to_safe_id = Column(String(20), ForeignKey('safes.id'), nullable=False)
    
    amount = Column(Numeric(15, 2), nullable=False)
    transfer_date = Column(DateTime, default=func.now())
    notes = Column(Text)
    
    # سندات مرتبطة
    from_voucher_id = Column(String(20), ForeignKey('vouchers.id'))  # سند الصرف
    to_voucher_id = Column(String(20), ForeignKey('vouchers.id'))    # سند القبض
    
    created_at = Column(DateTime, default=func.now())
    created_by = Column(String(100))  # اسم المستخدم
    
    # العلاقات
    from_project = db.relationship('Project', foreign_keys=[from_project_id], backref='transfers_out')
    to_project = db.relationship('Project', foreign_keys=[to_project_id], backref='transfers_in')
    from_safe = db.relationship('Safe', foreign_keys=[from_safe_id], backref='inter_transfers_out')
    to_safe = db.relationship('Safe', foreign_keys=[to_safe_id], backref='inter_transfers_in')
    from_voucher = db.relationship('Voucher', foreign_keys=[from_voucher_id])
    to_voucher = db.relationship('Voucher', foreign_keys=[to_voucher_id])
    
    def __repr__(self):
        return f'<InterProjectTransfer {self.amount} from {self.from_project_id} to {self.to_project_id}>'