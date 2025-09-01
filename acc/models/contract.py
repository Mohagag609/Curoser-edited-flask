from acc.extensions import db
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, Date, DateTime, func, Text, Boolean, Enum
from sqlalchemy.orm import relationship, validates
from decimal import Decimal
import enum

class ContractStatus(enum.Enum):
    """حالات العقد"""
    DRAFT = "مسودة"
    ACTIVE = "نشط"
    SUSPENDED = "معلق"
    COMPLETED = "مكتمل"
    CANCELLED = "ملغي"

class PaymentType(enum.Enum):
    """أنواع الدفع"""
    CASH = "نقدي"
    INSTALLMENT = "أقساط"
    MIXED = "مختلط"

class InstallmentPeriod(enum.Enum):
    """فترات الأقساط"""
    MONTHLY = "شهري"
    QUARTERLY = "ربع سنوي"
    SEMI_ANNUAL = "نصف سنوي"
    ANNUAL = "سنوي"
    CUSTOM = "مخصص"

class Contract(db.Model):
    """نموذج العقود المحسّن"""
    __tablename__ = 'contracts'
    __table_args__ = {"extend_existing": True}
    
    # المعرفات الأساسية
    id = Column(String(20), primary_key=True)
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    
    # بيانات الأطراف
    unit_id = Column(String(20), ForeignKey('units.id'), nullable=False, index=True)
    customer_id = Column(String(20), ForeignKey('customers.id'), nullable=False, index=True)
    
    # البيانات المالية الأساسية
    unit_price = Column(Numeric(15, 2), nullable=False)  # سعر الوحدة الأصلي
    total_price = Column(Numeric(15, 2), nullable=False)  # السعر الإجمالي بعد الإضافات
    discount_amount = Column(Numeric(15, 2), default=0)
    discount_percent = Column(Numeric(5, 2), default=0)
    final_price = Column(Numeric(15, 2), nullable=False)  # السعر النهائي بعد الخصم
    
    # الدفعات
    down_payment = Column(Numeric(15, 2), default=0)
    down_payment_percent = Column(Numeric(5, 2), default=0)
    maintenance_deposit = Column(Numeric(15, 2), default=0)
    
    # العمولات
    broker_id = Column(String(20), ForeignKey('brokers.id'), nullable=True)
    broker_name = Column(String(200))  # للحفظ التاريخي
    broker_percent = Column(Numeric(5, 2), default=0)
    broker_amount = Column(Numeric(15, 2), default=0)
    commission_paid = Column(Boolean, default=False)
    commission_payment_date = Column(Date)
    commission_safe_id = Column(String(20), ForeignKey('treasury.id'))
    
    # تفاصيل الأقساط
    payment_type = Column(Enum(PaymentType), nullable=False)
    installment_type = Column(Enum(InstallmentPeriod))
    installment_count = Column(Integer, default=0)
    installment_amount = Column(Numeric(15, 2), default=0)  # قيمة القسط الواحد
    
    # الدفعات الإضافية
    extra_annual_payments = Column(Integer, default=0)
    annual_payment_value = Column(Numeric(15, 2), default=0)
    
    # التواريخ
    contract_date = Column(Date, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    delivery_date = Column(Date)
    
    # الحالة والملاحظات
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT)
    notes = Column(Text)
    terms_conditions = Column(Text)
    
    # التدقيق
    created_by = Column(String(20))
    approved_by = Column(String(20))
    approval_date = Column(DateTime)
    
    # الطوابع الزمنية
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # العلاقات
    project = relationship('Project', backref='contracts')
    unit = relationship('Unit', backref='contract', uselist=False)
    customer = relationship('Customer', backref='contracts')
    broker = relationship('Broker', backref='contracts')
    installments = relationship('Installment', back_populates='contract', cascade='all, delete-orphan')
    payments = relationship('Payment', back_populates='contract')
    documents = relationship('ContractDocument', back_populates='contract', cascade='all, delete-orphan')
    
    # خصائص محسوبة
    @property
    def paid_amount(self):
        """المبلغ المدفوع"""
        from acc.models import Payment
        payments = Payment.query.filter_by(contract_id=self.id, status='completed').all()
        return sum(p.amount for p in payments)
    
    @property
    def remaining_amount(self):
        """المبلغ المتبقي"""
        return self.final_price - self.paid_amount
    
    @property
    def completion_percentage(self):
        """نسبة الإنجاز"""
        if self.final_price == 0:
            return 0
        return round((self.paid_amount / self.final_price) * 100, 2)
    
    @property
    def is_overdue(self):
        """هل يوجد أقساط متأخرة"""
        from datetime import date
        overdue = self.installments.filter(
            Installment.due_date < date.today(),
            Installment.status != 'paid'
        ).count()
        return overdue > 0
    
    @property
    def next_installment(self):
        """القسط التالي"""
        from datetime import date
        return self.installments.filter(
            Installment.status != 'paid'
        ).order_by(Installment.due_date).first()
    
    # التحقق من البيانات
    @validates('discount_percent')
    def validate_discount_percent(self, key, value):
        if value and (value < 0 or value > 100):
            raise ValueError("نسبة الخصم يجب أن تكون بين 0 و 100")
        return value
    
    @validates('broker_percent')
    def validate_broker_percent(self, key, value):
        if value and (value < 0 or value > 100):
            raise ValueError("نسبة العمولة يجب أن تكون بين 0 و 100")
        return value
    
    def calculate_prices(self):
        """حساب الأسعار تلقائياً"""
        # حساب قيمة الخصم
        if self.discount_percent:
            self.discount_amount = self.unit_price * (self.discount_percent / 100)
        
        # حساب السعر النهائي
        self.final_price = self.unit_price - self.discount_amount
        
        # حساب عمولة الوسيط
        if self.broker_percent:
            self.broker_amount = self.final_price * (self.broker_percent / 100)
        
        # حساب الدفعة الأولى
        if self.down_payment_percent:
            self.down_payment = self.final_price * (self.down_payment_percent / 100)
    
    def generate_installments(self):
        """توليد الأقساط تلقائياً"""
        from acc.models import Installment
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        
        if self.payment_type != PaymentType.INSTALLMENT:
            return []
        
        # حذف الأقساط القديمة
        Installment.query.filter_by(contract_id=self.id).delete()
        
        # حساب المبلغ المتبقي بعد الدفعة الأولى
        remaining = self.final_price - self.down_payment - self.maintenance_deposit
        
        # حساب قيمة القسط
        total_installments = self.installment_count
        if total_installments > 0:
            installment_amount = remaining / total_installments
        else:
            return []
        
        installments = []
        current_date = self.start_date
        
        # توليد الأقساط العادية
        for i in range(total_installments):
            # حساب تاريخ الاستحقاق
            if self.installment_type == InstallmentPeriod.MONTHLY:
                due_date = current_date + relativedelta(months=i+1)
            elif self.installment_type == InstallmentPeriod.QUARTERLY:
                due_date = current_date + relativedelta(months=(i+1)*3)
            elif self.installment_type == InstallmentPeriod.SEMI_ANNUAL:
                due_date = current_date + relativedelta(months=(i+1)*6)
            elif self.installment_type == InstallmentPeriod.ANNUAL:
                due_date = current_date + relativedelta(years=i+1)
            else:
                due_date = current_date + relativedelta(months=i+1)
            
            installment = Installment(
                contract_id=self.id,
                installment_number=i+1,
                amount=installment_amount,
                due_date=due_date,
                type='regular',
                description=f'قسط {i+1} من {total_installments}'
            )
            installments.append(installment)
        
        # توليد الدفعات السنوية الإضافية
        for i in range(self.extra_annual_payments):
            due_date = self.start_date + relativedelta(years=i+1)
            installment = Installment(
                contract_id=self.id,
                installment_number=total_installments + i + 1,
                amount=self.annual_payment_value,
                due_date=due_date,
                type='annual_extra',
                description=f'دفعة سنوية {i+1}'
            )
            installments.append(installment)
        
        # إضافة وديعة الصيانة كقسط أخير
        if self.maintenance_deposit > 0:
            last_date = self.end_date or (self.start_date + relativedelta(years=5))
            installment = Installment(
                contract_id=self.id,
                installment_number=total_installments + self.extra_annual_payments + 1,
                amount=self.maintenance_deposit,
                due_date=last_date,
                type='maintenance',
                description='وديعة الصيانة'
            )
            installments.append(installment)
        
        # حفظ الأقساط
        db.session.add_all(installments)
        db.session.commit()
        
        return installments
    
    def __repr__(self):
        return f'<Contract {self.code} - {self.customer.name if self.customer else ""}>'

# نموذج وثائق العقد
class ContractDocument(db.Model):
    """وثائق العقد"""
    __tablename__ = 'contract_documents'
    
    id = Column(Integer, primary_key=True)
    contract_id = Column(String(20), ForeignKey('contracts.id'), nullable=False)
    document_type = Column(String(50), nullable=False)  # صورة العقد، مخطط، إيصال، الخ
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=False)
    uploaded_at = Column(DateTime, default=func.now())
    uploaded_by = Column(String(20))
    
    contract = relationship('Contract', back_populates='documents')
