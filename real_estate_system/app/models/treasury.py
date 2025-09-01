from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Numeric, ForeignKey, Boolean, index
from sqlalchemy.orm import relationship


class Safe(BaseModel):
    """نموذج الخزينة"""
    __tablename__ = 'safes'
    
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    initial_balance = Column(Numeric(15, 2), default=0)
    current_balance = Column(Numeric(15, 2), default=0)
    status = Column(String(20), default='نشط', index=True)
    is_main = Column(Boolean, default=False)
    
    # Relationships
    project = relationship('Project', backref='safe_projects')
    transfers_from = relationship('SafeTransfer', foreign_keys='SafeTransfer.from_safe_id', backref='from_safe')
    transfers_to = relationship('SafeTransfer', foreign_keys='SafeTransfer.to_safe_id', backref='to_safe')
    vouchers = relationship('Voucher', backref='safe', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Safe {self.name}>'
    
    @property
    def total_income(self):
        """إجمالي الإيرادات"""
        from sqlalchemy import func
        result = db.session.query(func.sum(Voucher.amount)).filter_by(
            safe_id=self.id,
            voucher_type='إيراد'
        ).scalar()
        return float(result) if result else 0.0
    
    @property
    def total_expenses(self):
        """إجمالي المصروفات"""
        from sqlalchemy import func
        result = db.session.query(func.sum(Voucher.amount)).filter_by(
            safe_id=self.id,
            voucher_type='مصروف'
        ).scalar()
        return float(result) if result else 0.0
    
    @property
    def net_balance(self):
        """الرصيد الصافي"""
        return self.initial_balance + self.total_income - self.total_expenses
    
    def add_income(self, amount, description=None, reference=None):
        """إضافة إيراد"""
        from app.models.voucher import Voucher
        voucher = Voucher(
            safe_id=self.id,
            amount=amount,
            voucher_type='إيراد',
            description=description,
            reference=reference
        )
        voucher.save()
        self.update_balance()
        return voucher
    
    def add_expense(self, amount, description=None, reference=None):
        """إضافة مصروف"""
        from app.models.voucher import Voucher
        voucher = Voucher(
            safe_id=self.id,
            amount=amount,
            voucher_type='مصروف',
            description=description,
            reference=reference
        )
        voucher.save()
        self.update_balance()
        return voucher
    
    def transfer_to(self, to_safe, amount, description=None):
        """تحويل إلى خزينة أخرى"""
        if self.current_balance < amount:
            raise ValueError("الرصيد غير كافي")
        
        transfer = SafeTransfer(
            from_safe_id=self.id,
            to_safe_id=to_safe.id,
            amount=amount,
            description=description
        )
        transfer.save()
        
        # تحديث الأرصدة
        self.current_balance -= amount
        to_safe.current_balance += amount
        self.save()
        to_safe.save()
        
        return transfer
    
    def update_balance(self):
        """تحديث الرصيد الحالي"""
        self.current_balance = self.net_balance
        self.save()
    
    def to_dict(self):
        """تحويل الخزينة إلى قاموس"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'initial_balance': float(self.initial_balance) if self.initial_balance else 0,
            'current_balance': float(self.current_balance) if self.current_balance else 0,
            'status': self.status,
            'is_main': self.is_main,
            'total_income': self.total_income,
            'total_expenses': self.total_expenses,
            'net_balance': self.net_balance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SafeTransfer(BaseModel):
    """تحويل بين الخزائن"""
    __tablename__ = 'safe_transfers'
    
    from_safe_id = Column(String(20), ForeignKey('safes.id'), nullable=False, index=True)
    to_safe_id = Column(String(20), ForeignKey('safes.id'), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text)
    status = Column(String(20), default='مكتمل', index=True)
    
    def __repr__(self):
        return f'<SafeTransfer {self.from_safe.name} -> {self.to_safe.name} - {self.amount}>'
    
    @property
    def is_completed(self):
        """هل التحويل مكتمل؟"""
        return self.status == 'مكتمل'
    
    def to_dict(self):
        """تحويل التحويل إلى قاموس"""
        return {
            'id': self.id,
            'from_safe_id': self.from_safe_id,
            'to_safe_id': self.to_safe_id,
            'amount': float(self.amount) if self.amount else 0,
            'description': self.description,
            'status': self.status,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }