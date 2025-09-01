from acc.extensions import db
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, Date, DateTime, func, Text, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

class InstallmentStatus(enum.Enum):
    """حالات القسط"""
    PENDING = "مستحق"
    PAID = "مدفوع"
    PARTIAL = "مدفوع جزئياً"
    OVERDUE = "متأخر"
    CANCELLED = "ملغي"

class InstallmentType(enum.Enum):
    """أنواع الأقساط"""
    REGULAR = "عادي"
    DOWN_PAYMENT = "دفعة أولى"
    ANNUAL_EXTRA = "دفعة سنوية"
    MAINTENANCE = "وديعة صيانة"
    PENALTY = "غرامة تأخير"
    CUSTOM = "مخصص"

class Installment(db.Model):
    """نموذج الأقساط المحسّن"""
    __tablename__ = 'installments'
    __table_args__ = {"extend_existing": True}
    
    # المعرفات الأساسية
    id = Column(String(20), primary_key=True)
    contract_id = Column(String(20), ForeignKey('contracts.id'), nullable=False, index=True)
    installment_number = Column(Integer, nullable=False)
    
    # البيانات المالية
    original_amount = Column(Numeric(15, 2), nullable=False)  # المبلغ الأصلي
    amount = Column(Numeric(15, 2), nullable=False)  # المبلغ المستحق
    paid_amount = Column(Numeric(15, 2), default=0)  # المبلغ المدفوع
    penalty_amount = Column(Numeric(15, 2), default=0)  # غرامة التأخير
    discount_amount = Column(Numeric(15, 2), default=0)  # خصم على القسط
    
    # التواريخ
    due_date = Column(Date, nullable=False, index=True)
    paid_date = Column(Date)
    grace_period_days = Column(Integer, default=0)  # فترة السماح
    
    # التفاصيل
    type = Column(Enum(InstallmentType), default=InstallmentType.REGULAR)
    status = Column(Enum(InstallmentStatus), default=InstallmentStatus.PENDING, index=True)
    description = Column(String(500))
    notes = Column(Text)
    
    # معلومات الدفع
    payment_method = Column(String(50))  # نقدي، شيك، تحويل، الخ
    payment_reference = Column(String(100))  # رقم الشيك أو التحويل
    collected_by = Column(String(20), ForeignKey('users.id'))
    
    # التدقيق
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # العلاقات
    contract = relationship('Contract', back_populates='installments')
    payments = relationship('InstallmentPayment', back_populates='installment', cascade='all, delete-orphan')
    reminders = relationship('InstallmentReminder', back_populates='installment', cascade='all, delete-orphan')
    
    # خصائص محسوبة
    @property
    def remaining_amount(self):
        """المبلغ المتبقي"""
        return self.amount + self.penalty_amount - self.paid_amount - self.discount_amount
    
    @property
    def is_overdue(self):
        """هل القسط متأخر"""
        from datetime import date, timedelta
        grace_date = self.due_date + timedelta(days=self.grace_period_days)
        return date.today() > grace_date and self.status not in [InstallmentStatus.PAID, InstallmentStatus.CANCELLED]
    
    @property
    def days_overdue(self):
        """عدد أيام التأخير"""
        from datetime import date
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days
    
    @property
    def payment_percentage(self):
        """نسبة السداد"""
        if self.amount == 0:
            return 100
        return round((self.paid_amount / self.amount) * 100, 2)
    
    def calculate_penalty(self, penalty_rate=0.02):
        """حساب غرامة التأخير"""
        if not self.is_overdue:
            return 0
        
        # حساب الغرامة (2% شهرياً افتراضياً)
        months_overdue = self.days_overdue // 30
        self.penalty_amount = self.amount * penalty_rate * months_overdue
        return self.penalty_amount
    
    def make_payment(self, amount, payment_method='cash', reference=None):
        """تسجيل دفعة"""
        from acc.models import InstallmentPayment
        
        if amount > self.remaining_amount:
            raise ValueError("المبلغ المدفوع أكبر من المستحق")
        
        payment = InstallmentPayment(
            installment_id=self.id,
            amount=amount,
            payment_method=payment_method,
            reference=reference
        )
        
        self.paid_amount += amount
        
        # تحديث الحالة
        if self.paid_amount >= self.amount:
            self.status = InstallmentStatus.PAID
            self.paid_date = date.today()
        elif self.paid_amount > 0:
            self.status = InstallmentStatus.PARTIAL
        
        db.session.add(payment)
        return payment
    
    def send_reminder(self):
        """إرسال تذكير"""
        from acc.models import InstallmentReminder
        
        reminder = InstallmentReminder(
            installment_id=self.id,
            sent_date=date.today(),
            method='sms'  # أو email
        )
        
        db.session.add(reminder)
        return reminder
    
    def __repr__(self):
        return f'<Installment {self.installment_number} - {self.contract.code if self.contract else ""}>'

# نموذج دفعات الأقساط
class InstallmentPayment(db.Model):
    """دفعات الأقساط"""
    __tablename__ = 'installment_payments'
    
    id = Column(Integer, primary_key=True)
    installment_id = Column(String(20), ForeignKey('installments.id'), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_date = Column(DateTime, default=func.now())
    payment_method = Column(String(50))
    reference = Column(String(100))
    notes = Column(Text)
    created_by = Column(String(20), ForeignKey('users.id'))
    
    installment = relationship('Installment', back_populates='payments')

# نموذج تذكيرات الأقساط
class InstallmentReminder(db.Model):
    """تذكيرات الأقساط"""
    __tablename__ = 'installment_reminders'
    
    id = Column(Integer, primary_key=True)
    installment_id = Column(String(20), ForeignKey('installments.id'), nullable=False)
    sent_date = Column(Date, nullable=False)
    method = Column(String(50))  # sms, email, phone
    status = Column(String(50))  # sent, failed, pending
    response = Column(Text)
    
    installment = relationship('Installment', back_populates='reminders')
