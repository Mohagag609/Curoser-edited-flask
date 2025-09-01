from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Text, Numeric, index
from sqlalchemy.orm import relationship


class Broker(BaseModel):
    """نموذج الوسيط"""
    __tablename__ = 'brokers'
    
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    phone = Column(String(20), index=True)
    national_id = Column(String(20), index=True)
    address = Column(Text)
    email = Column(String(100), index=True)
    status = Column(String(20), default='نشط', index=True)
    notes = Column(Text)
    commission_rate = Column(Numeric(5, 2), default=0)  # نسبة العمولة
    
    # Relationships
    broker_dues = relationship('BrokerDue', backref='broker', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Broker {self.name}>'
    
    @property
    def total_contracts(self):
        """إجمالي عدد العقود"""
        from sqlalchemy import func
        result = db.session.query(func.count(Contract.id)).filter_by(broker_name=self.name).scalar()
        return result or 0
    
    @property
    def total_commission(self):
        """إجمالي العمولة"""
        from sqlalchemy import func
        result = db.session.query(func.sum(Contract.broker_amount)).filter_by(broker_name=self.name).scalar()
        return float(result) if result else 0.0
    
    @property
    def total_paid(self):
        """إجمالي المدفوع"""
        from sqlalchemy import func
        result = db.session.query(func.sum(BrokerDue.amount)).filter_by(
            broker_id=self.id,
            status='مدفوع'
        ).scalar()
        return float(result) if result else 0.0
    
    @property
    def total_due(self):
        """إجمالي المستحق"""
        from sqlalchemy import func
        result = db.session.query(func.sum(BrokerDue.amount)).filter_by(
            broker_id=self.id,
            status='مستحق'
        ).scalar()
        return float(result) if result else 0.0
    
    @property
    def remaining_due(self):
        """المستحق المتبقي"""
        return self.total_due - self.total_paid
    
    def add_due(self, amount, description=None, contract_id=None):
        """إضافة مستحق"""
        due = BrokerDue(
            broker_id=self.id,
            amount=amount,
            description=description,
            contract_id=contract_id
        )
        due.save()
        return due
    
    def mark_due_as_paid(self, due_id, payment_date=None, payment_method=None, payment_reference=None):
        """تسجيل المستحق كمدفوع"""
        due = self.broker_dues.filter_by(id=due_id).first()
        if due:
            due.mark_as_paid(payment_date, payment_method, payment_reference)
            return True
        return False
    
    def to_dict(self):
        """تحويل الوسيط إلى قاموس"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'phone': self.phone,
            'national_id': self.national_id,
            'address': self.address,
            'email': self.email,
            'status': self.status,
            'notes': self.notes,
            'commission_rate': float(self.commission_rate) if self.commission_rate else 0,
            'total_contracts': self.total_contracts,
            'total_commission': self.total_commission,
            'total_paid': self.total_paid,
            'total_due': self.total_due,
            'remaining_due': self.remaining_due,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BrokerDue(BaseModel):
    """مستحق الوسيط"""
    __tablename__ = 'broker_dues'
    
    broker_id = Column(String(20), ForeignKey('brokers.id'), nullable=False, index=True)
    contract_id = Column(String(20), ForeignKey('contracts.id'), nullable=True, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text)
    status = Column(String(20), default='مستحق', index=True)  # مستحق، مدفوع
    payment_date = Column(Date)
    payment_method = Column(String(50))
    payment_reference = Column(String(100))
    
    def __repr__(self):
        return f'<BrokerDue {self.broker.name} - {self.amount}>'
    
    @property
    def is_paid(self):
        """هل المستحق مدفوع؟"""
        return self.status == 'مدفوع'
    
    def mark_as_paid(self, payment_date=None, payment_method=None, payment_reference=None):
        """تسجيل المستحق كمدفوع"""
        from datetime import date
        self.status = 'مدفوع'
        self.payment_date = payment_date or date.today()
        self.payment_method = payment_method
        self.payment_reference = payment_reference
        self.save()
    
    def to_dict(self):
        """تحويل المستحق إلى قاموس"""
        return {
            'id': self.id,
            'broker_id': self.broker_id,
            'contract_id': self.contract_id,
            'amount': float(self.amount) if self.amount else 0,
            'description': self.description,
            'status': self.status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
            'is_paid': self.is_paid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }