from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Numeric, ForeignKey, Date, Boolean, index
from sqlalchemy.orm import relationship


class Contract(BaseModel):
    """نموذج العقد"""
    __tablename__ = 'contracts'
    
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    unit_id = Column(String(20), ForeignKey('units.id'), nullable=False, index=True)
    customer_id = Column(String(20), ForeignKey('customers.id'), nullable=False, index=True)
    total_price = Column(Numeric(15, 2), nullable=False)
    down_payment = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    maintenance_deposit = Column(Numeric(15, 2), default=0)
    broker_name = Column(String(200))
    broker_percent = Column(Numeric(5, 2), default=0)
    broker_amount = Column(Numeric(15, 2), default=0)
    commission_safe_id = Column(String(20), ForeignKey('safes.id'))
    contract_date = Column(Date, nullable=False)
    status = Column(String(50), default='نشط', index=True)
    notes = Column(Text)
    is_cancelled = Column(Boolean, default=False)
    cancellation_date = Column(Date)
    cancellation_reason = Column(Text)
    
    # Relationships
    unit = relationship('Unit', backref='contract_units')
    customer = relationship('Customer', backref='contract_customers')
    project = relationship('Project', backref='contract_projects')
    commission_safe = relationship('Safe', foreign_keys=[commission_safe_id], backref='commission_contracts')
    installments = relationship('Installment', backref='contract', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Contract {self.code}>'
    
    @property
    def remaining_amount(self):
        """المبلغ المتبقي"""
        paid_amount = sum(installment.amount for installment in self.installments.filter_by(status='مدفوع'))
        return float(self.total_price - paid_amount)
    
    @property
    def paid_amount(self):
        """المبلغ المدفوع"""
        return sum(installment.amount for installment in self.installments.filter_by(status='مدفوع'))
    
    @property
    def pending_installments(self):
        """الأقساط المعلقة"""
        return self.installments.filter_by(status='معلق').count()
    
    @property
    def paid_installments(self):
        """الأقساط المدفوعة"""
        return self.installments.filter_by(status='مدفوع').count()
    
    @property
    def total_installments(self):
        """إجمالي الأقساط"""
        return self.installments.count()
    
    @property
    def is_fully_paid(self):
        """هل العقد مدفوع بالكامل؟"""
        return self.remaining_amount <= 0
    
    @property
    def payment_percentage(self):
        """نسبة الدفع"""
        if self.total_price > 0:
            return round((self.paid_amount / float(self.total_price)) * 100, 2)
        return 0
    
    @property
    def net_amount(self):
        """المبلغ الصافي (بعد الخصم)"""
        return float(self.total_price - self.discount_amount)
    
    @property
    def total_amount_with_deposits(self):
        """إجمالي المبلغ مع الودائع"""
        return float(self.total_price + self.maintenance_deposit)
    
    def get_installments_by_status(self, status):
        """الحصول على الأقساط حسب الحالة"""
        return self.installments.filter_by(status=status).all()
    
    def get_next_installment(self):
        """الحصول على القسط التالي"""
        return self.installments.filter_by(status='معلق').order_by(Installment.due_date).first()
    
    def get_overdue_installments(self):
        """الحصول على الأقساط المتأخرة"""
        from datetime import date
        return self.installments.filter(
            Installment.status == 'معلق',
            Installment.due_date < date.today()
        ).all()
    
    def cancel_contract(self, reason=None):
        """إلغاء العقد"""
        from datetime import date
        self.is_cancelled = True
        self.cancellation_date = date.today()
        self.cancellation_reason = reason
        self.status = 'ملغي'
        self.save()
    
    def to_dict(self):
        """تحويل العقد إلى قاموس"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'code': self.code,
            'unit_id': self.unit_id,
            'customer_id': self.customer_id,
            'total_price': float(self.total_price) if self.total_price else 0,
            'down_payment': float(self.down_payment) if self.down_payment else 0,
            'discount_amount': float(self.discount_amount) if self.discount_amount else 0,
            'maintenance_deposit': float(self.maintenance_deposit) if self.maintenance_deposit else 0,
            'broker_name': self.broker_name,
            'broker_percent': float(self.broker_percent) if self.broker_percent else 0,
            'broker_amount': float(self.broker_amount) if self.broker_amount else 0,
            'commission_safe_id': self.commission_safe_id,
            'contract_date': self.contract_date.isoformat() if self.contract_date else None,
            'status': self.status,
            'notes': self.notes,
            'is_cancelled': self.is_cancelled,
            'cancellation_date': self.cancellation_date.isoformat() if self.cancellation_date else None,
            'cancellation_reason': self.cancellation_reason,
            'remaining_amount': self.remaining_amount,
            'paid_amount': self.paid_amount,
            'pending_installments': self.pending_installments,
            'paid_installments': self.paid_installments,
            'total_installments': self.total_installments,
            'is_fully_paid': self.is_fully_paid,
            'payment_percentage': self.payment_percentage,
            'net_amount': self.net_amount,
            'total_amount_with_deposits': self.total_amount_with_deposits,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }