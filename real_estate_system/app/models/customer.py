from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Text, index


class Customer(BaseModel):
    """نموذج العميل"""
    __tablename__ = 'customers'
    
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    phone = Column(String(20), index=True)
    national_id = Column(String(20), index=True)
    address = Column(Text)
    status = Column(String(20), default='نشط', index=True)
    notes = Column(Text)
    
    # Relationships
    contracts = db.relationship('Contract', backref='customer', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Customer {self.name}>'
    
    @property
    def total_contracts(self):
        """إجمالي عدد العقود"""
        return self.contracts.count()
    
    @property
    def total_contracts_value(self):
        """إجمالي قيمة العقود"""
        from sqlalchemy import func
        result = db.session.query(func.sum(Contract.total_price)).filter_by(customer_id=self.id).scalar()
        return float(result) if result else 0.0
    
    @property
    def total_paid_amount(self):
        """إجمالي المبلغ المدفوع"""
        from sqlalchemy import func
        result = db.session.query(func.sum(Installment.amount)).join(Contract).filter(
            Contract.customer_id == self.id,
            Installment.status == 'مدفوع'
        ).scalar()
        return float(result) if result else 0.0
    
    @property
    def remaining_amount(self):
        """المبلغ المتبقي"""
        return self.total_contracts_value - self.total_paid_amount
    
    def get_contracts_by_status(self, status):
        """الحصول على العقود حسب الحالة"""
        return self.contracts.filter_by(status=status).all()
    
    def get_installments_by_status(self, status):
        """الحصول على الأقساط حسب الحالة"""
        return db.session.query(Installment).join(Contract).filter(
            Contract.customer_id == self.id,
            Installment.status == status
        ).all()
    
    def to_dict(self):
        """تحويل العميل إلى قاموس"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'phone': self.phone,
            'national_id': self.national_id,
            'address': self.address,
            'status': self.status,
            'notes': self.notes,
            'total_contracts': self.total_contracts,
            'total_contracts_value': self.total_contracts_value,
            'total_paid_amount': self.total_paid_amount,
            'remaining_amount': self.remaining_amount,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }