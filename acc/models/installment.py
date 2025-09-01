from acc.extensions import db
from sqlalchemy import Integer, Column, String, Numeric, ForeignKey, Date, DateTime, func, Boolean
from datetime import date


class Installment(db.Model):
    """نموذج الأقساط المحسن"""
    __tablename__ = 'installments'
    
    # المفاتيح الأساسية
    id = Column(String(20), primary_key=True)
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False, index=True)
    contract_id = Column(String(20), ForeignKey('contracts.id'), index=True)
    unit_id = Column(String(20), ForeignKey('units.id'), nullable=False, index=True)
    customer_id = Column(String(20), ForeignKey('customers.id'), index=True)
    
    # بيانات القسط
    installment_number = Column(Integer, nullable=False)
    type = Column(String(50), nullable=False)  # شهري/ربع سنوي/سنوي/صيانة
    original_amount = Column(Numeric(15, 2), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)  # المبلغ المتبقي
    paid_amount = Column(Numeric(15, 2), default=0)  # المبلغ المدفوع
    
    # التواريخ
    due_date = Column(Date, nullable=False, index=True)
    paid_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # الحالة
    status = Column(String(20), default='مستحق', index=True)
    is_overdue = Column(Boolean, default=False, index=True)
    notes = Column(String(500))
    
    # العلاقات المحسنة
    project = db.relationship('Project', backref='installments')
    contract = db.relationship('Contract', foreign_keys=[contract_id], backref='installments')
    unit = db.relationship('Unit', backref='installments')
    customer = db.relationship('Customer', foreign_keys=[customer_id], backref='installments')
    
    def __repr__(self):
        return f'<Installment {self.id} - {self.amount} - {self.status}>'
    
    @property
    def is_paid(self):
        """هل القسط مدفوع بالكامل؟"""
        return self.paid_amount >= self.original_amount
    
    @property
    def is_partially_paid(self):
        """هل القسط مدفوع جزئياً؟"""
        return 0 < self.paid_amount < self.original_amount
    
    @property
    def is_overdue_check(self):
        """هل القسط متأخر؟"""
        return self.due_date < date.today() and not self.is_paid
    
    def update_status(self):
        """تحديث حالة القسط"""
        if self.is_paid:
            self.status = 'مدفوع'
            self.is_overdue = False
        elif self.is_partially_paid:
            self.status = 'مدفوع جزئياً'
            self.is_overdue = self.is_overdue_check
        else:
            self.status = 'مستحق' if not self.is_overdue_check else 'متأخر'
            self.is_overdue = self.is_overdue_check
    
    def add_payment(self, amount, payment_date=None):
        """إضافة دفعة للقسط"""
        if payment_date is None:
            payment_date = date.today()
        
        self.paid_amount += amount
        self.amount = self.original_amount - self.paid_amount
        
        if self.is_paid:
            self.paid_date = payment_date
        
        self.update_status()
        db.session.commit()
    
    @classmethod
    def get_overdue_installments(cls, project_id=None):
        """الحصول على الأقساط المتأخرة"""
        query = cls.query.filter(cls.is_overdue == True)
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.all()
    
    @classmethod
    def get_due_installments(cls, project_id=None, days_ahead=7):
        """الحصول على الأقساط المستحقة خلال الأيام القادمة"""
        from datetime import timedelta
        target_date = date.today() + timedelta(days=days_ahead)
        
        query = cls.query.filter(
            cls.due_date <= target_date,
            cls.due_date >= date.today(),
            cls.status.in_(['مستحق', 'مدفوع جزئياً'])
        )
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.all()