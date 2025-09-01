from acc.extensions import db
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, Date, DateTime, func, Boolean, Text
from datetime import date


class Contract(db.Model):
    """نموذج العقود المحسن"""
    __tablename__ = 'contracts'
    
    # المفاتيح الأساسية
    id = Column(String(20), primary_key=True)
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    unit_id = Column(String(20), ForeignKey('units.id'), nullable=False, index=True)
    customer_id = Column(String(20), ForeignKey('customers.id'), nullable=False, index=True)
    
    # البيانات المالية
    total_price = Column(Numeric(15, 2), nullable=False)
    down_payment = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    maintenance_deposit = Column(Numeric(15, 2), default=0)
    net_price = Column(Numeric(15, 2))  # السعر الصافي بعد الخصم
    
    # بيانات الوسيط
    broker_name = Column(String(200))
    broker_percent = Column(Numeric(5, 2), default=0)
    broker_amount = Column(Numeric(15, 2), default=0)
    commission_safe_id = Column(String(20), ForeignKey('safes.id'))
    
    # نظام الدفع
    payment_type = Column(String(20), nullable=False)  # نقدي/أقساط
    installment_type = Column(String(20))  # شهري/ربع سنوي/نصف سنوي/سنوي
    installment_count = Column(Integer, default=0)
    installment_amount = Column(Numeric(15, 2), default=0)
    extra_annual = Column(Integer, default=0)
    annual_payment_value = Column(Numeric(15, 2), default=0)
    
    # التواريخ
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    signed_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # الحالة والمعلومات الإضافية
    status = Column(String(20), default='نشط', index=True)
    is_active = Column(Boolean, default=True, index=True)
    notes = Column(Text)
    contract_file_path = Column(String(500))  # مسار ملف العقد
    
    # العلاقات المحسنة
    project = db.relationship('Project', backref=db.backref('contracts', lazy='dynamic'))
    unit = db.relationship('Unit', backref=db.backref('contracts', lazy='dynamic'))
    customer = db.relationship('Customer', backref=db.backref('contracts', lazy='dynamic'))
    commission_safe = db.relationship('Safe', backref=db.backref('commission_contracts', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Contract {self.code} - {self.customer.name if self.customer else "Unknown"}>'
    
    @property
    def installments(self):
        """الحصول على أقساط العقد"""
        from acc.models import Installment
        return Installment.query.filter_by(contract_id=self.id).order_by(Installment.installment_number)
    
    @property
    def total_paid_amount(self):
        """إجمالي المبلغ المدفوع"""
        return sum(installment.paid_amount for installment in self.installments)
    
    @property
    def remaining_amount(self):
        """المبلغ المتبقي"""
        return self.net_price - self.total_paid_amount
    
    @property
    def payment_progress(self):
        """نسبة التقدم في الدفع"""
        if self.net_price == 0:
            return 0
        return (self.total_paid_amount / self.net_price) * 100
    
    def calculate_net_price(self):
        """حساب السعر الصافي"""
        self.net_price = self.total_price - self.discount_amount
        return self.net_price
    
    def generate_installments(self):
        """إنشاء أقساط العقد"""
        if self.payment_type != 'أقساط' or self.installment_count == 0:
            return
        
        from acc.models import Installment
        from acc.services.code_generator import generate_installment_code
        from datetime import timedelta
        
        # حذف الأقساط الموجودة
        Installment.query.filter_by(contract_id=self.id).delete()
        
        # حساب مبلغ القسط
        installment_amount = self.net_price / self.installment_count
        
        # إنشاء الأقساط
        for i in range(1, self.installment_count + 1):
            installment = Installment(
                id=generate_installment_code(),
                project_id=self.project_id,
                contract_id=self.id,
                unit_id=self.unit_id,
                customer_id=self.customer_id,
                installment_number=i,
                type=self.installment_type,
                original_amount=installment_amount,
                amount=installment_amount,
                due_date=self.start_date + timedelta(days=30 * i)  # شهرياً
            )
            db.session.add(installment)
        
        db.session.commit()
    
    def update_status(self):
        """تحديث حالة العقد"""
        if self.remaining_amount <= 0:
            self.status = 'مكتمل'
            self.is_active = False
        elif self.total_paid_amount > 0:
            self.status = 'قيد التنفيذ'
        else:
            self.status = 'نشط'
    
    @classmethod
    def get_active_contracts(cls, project_id=None):
        """الحصول على العقود النشطة"""
        query = cls.query.filter_by(is_active=True)
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.all()
    
    @classmethod
    def get_overdue_contracts(cls, project_id=None):
        """الحصول على العقود المتأخرة"""
        from acc.models import Installment
        overdue_installments = Installment.get_overdue_installments(project_id)
        contract_ids = [inst.contract_id for inst in overdue_installments if inst.contract_id]
        return cls.query.filter(cls.id.in_(contract_ids)).all()