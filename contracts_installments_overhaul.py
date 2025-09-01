#!/usr/bin/env python3
"""
إصلاح شامل وجذري لنظام العقود والأقساط
Complete Overhaul of Contracts and Installments System
"""

import os
import shutil
from datetime import datetime

def create_backup():
    """إنشاء نسخة احتياطية من الملفات الحالية"""
    print("📦 إنشاء نسخة احتياطية...")
    
    backup_dir = f"/workspace/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # نسخ الملفات المهمة
    files_to_backup = [
        "/workspace/acc/models/contract.py",
        "/workspace/acc/models/installment.py",
        "/workspace/acc/blueprints/contracts/routes.py",
        "/workspace/acc/blueprints/installments/routes.py"
    ]
    
    for file in files_to_backup:
        if os.path.exists(file):
            dest = os.path.join(backup_dir, os.path.basename(file))
            shutil.copy2(file, dest)
            print(f"  ✅ تم نسخ {os.path.basename(file)}")
    
    return backup_dir

def create_enhanced_contract_model():
    """إنشاء نموذج محسّن للعقود"""
    print("\n🔧 إنشاء نموذج محسّن للعقود...")
    
    enhanced_model = '''from acc.extensions import db
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
    created_by = Column(String(20), ForeignKey('users.id'))
    approved_by = Column(String(20), ForeignKey('users.id'))
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
    uploaded_by = Column(String(20), ForeignKey('users.id'))
    
    contract = relationship('Contract', back_populates='documents')
'''
    
    # حفظ النموذج المحسّن
    model_path = "/workspace/acc/models/contract_enhanced.py"
    with open(model_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_model)
    
    print(f"  ✅ تم إنشاء {model_path}")
    return model_path

def create_enhanced_installment_model():
    """إنشاء نموذج محسّن للأقساط"""
    print("\n🔧 إنشاء نموذج محسّن للأقساط...")
    
    enhanced_model = '''from acc.extensions import db
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
'''
    
    # حفظ النموذج المحسّن
    model_path = "/workspace/acc/models/installment_enhanced.py"
    with open(model_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_model)
    
    print(f"  ✅ تم إنشاء {model_path}")
    return model_path

def create_contract_templates():
    """إنشاء قوالب HTML احترافية للعقود"""
    print("\n🎨 إنشاء قوالب احترافية للعقود...")
    
    # إنشاء مجلد القوالب
    template_dir = "/workspace/acc/blueprints/contracts/templates/contracts"
    os.makedirs(template_dir, exist_ok=True)
    
    # قالب قائمة العقود
    index_template = '''{% extends "base.html" %}

{% block title %}إدارة العقود{% endblock %}

{% block content %}
<div class="container-fluid px-4">
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <div>
            <h1 class="h3 mb-0">إدارة العقود</h1>
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb mb-0">
                    <li class="breadcrumb-item"><a href="{{ url_for('dashboard.index') }}">الرئيسية</a></li>
                    <li class="breadcrumb-item active">العقود</li>
                </ol>
            </nav>
        </div>
        <div>
            <a href="{{ url_for('contracts.create') }}" class="btn btn-primary">
                <i class="fas fa-plus-circle me-2"></i>عقد جديد
            </a>
            <button class="btn btn-outline-secondary" onclick="exportContracts()">
                <i class="fas fa-download me-2"></i>تصدير
            </button>
        </div>
    </div>

    <!-- Statistics Cards -->
    <div class="row g-3 mb-4">
        <div class="col-12 col-sm-6 col-lg-3">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <div class="d-flex align-items-center">
                        <div class="flex-shrink-0">
                            <div class="bg-primary bg-opacity-10 p-3 rounded">
                                <i class="fas fa-file-contract text-primary fa-2x"></i>
                            </div>
                        </div>
                        <div class="flex-grow-1 ms-3">
                            <h6 class="text-muted mb-1">إجمالي العقود</h6>
                            <h3 class="mb-0">{{ stats.total_contracts }}</h3>
                            <small class="text-success">
                                <i class="fas fa-arrow-up me-1"></i>12% هذا الشهر
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-12 col-sm-6 col-lg-3">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <div class="d-flex align-items-center">
                        <div class="flex-shrink-0">
                            <div class="bg-success bg-opacity-10 p-3 rounded">
                                <i class="fas fa-check-circle text-success fa-2x"></i>
                            </div>
                        </div>
                        <div class="flex-grow-1 ms-3">
                            <h6 class="text-muted mb-1">عقود نشطة</h6>
                            <h3 class="mb-0">{{ stats.active_contracts }}</h3>
                            <small class="text-muted">{{ stats.active_percentage }}% من الإجمالي</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-12 col-sm-6 col-lg-3">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <div class="d-flex align-items-center">
                        <div class="flex-shrink-0">
                            <div class="bg-warning bg-opacity-10 p-3 rounded">
                                <i class="fas fa-clock text-warning fa-2x"></i>
                            </div>
                        </div>
                        <div class="flex-grow-1 ms-3">
                            <h6 class="text-muted mb-1">أقساط متأخرة</h6>
                            <h3 class="mb-0">{{ stats.overdue_installments }}</h3>
                            <small class="text-danger">{{ format_currency(stats.overdue_amount) }}</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-12 col-sm-6 col-lg-3">
            <div class="card border-0 shadow-sm h-100">
                <div class="card-body">
                    <div class="d-flex align-items-center">
                        <div class="flex-shrink-0">
                            <div class="bg-info bg-opacity-10 p-3 rounded">
                                <i class="fas fa-dollar-sign text-info fa-2x"></i>
                            </div>
                        </div>
                        <div class="flex-grow-1 ms-3">
                            <h6 class="text-muted mb-1">إجمالي قيمة العقود</h6>
                            <h5 class="mb-0">{{ format_currency(stats.total_value) }}</h5>
                            <small class="text-muted">محصل: {{ stats.collection_rate }}%</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Filters -->
    <div class="card border-0 shadow-sm mb-4">
        <div class="card-body">
            <form method="get" id="filterForm">
                <div class="row g-3">
                    <div class="col-md-3">
                        <label class="form-label">البحث</label>
                        <div class="input-group">
                            <span class="input-group-text"><i class="fas fa-search"></i></span>
                            <input type="text" class="form-control" name="search" 
                                   placeholder="رقم العقد، اسم العميل، الوحدة..."
                                   value="{{ request.args.get('search', '') }}">
                        </div>
                    </div>
                    
                    <div class="col-md-2">
                        <label class="form-label">الحالة</label>
                        <select class="form-select" name="status">
                            <option value="">جميع الحالات</option>
                            <option value="active" {% if request.args.get('status') == 'active' %}selected{% endif %}>نشط</option>
                            <option value="draft" {% if request.args.get('status') == 'draft' %}selected{% endif %}>مسودة</option>
                            <option value="completed" {% if request.args.get('status') == 'completed' %}selected{% endif %}>مكتمل</option>
                            <option value="cancelled" {% if request.args.get('status') == 'cancelled' %}selected{% endif %}>ملغي</option>
                        </select>
                    </div>
                    
                    <div class="col-md-2">
                        <label class="form-label">نوع الدفع</label>
                        <select class="form-select" name="payment_type">
                            <option value="">جميع الأنواع</option>
                            <option value="cash">نقدي</option>
                            <option value="installment">أقساط</option>
                            <option value="mixed">مختلط</option>
                        </select>
                    </div>
                    
                    <div class="col-md-2">
                        <label class="form-label">من تاريخ</label>
                        <input type="date" class="form-control" name="from_date" 
                               value="{{ request.args.get('from_date', '') }}">
                    </div>
                    
                    <div class="col-md-2">
                        <label class="form-label">إلى تاريخ</label>
                        <input type="date" class="form-control" name="to_date" 
                               value="{{ request.args.get('to_date', '') }}">
                    </div>
                    
                    <div class="col-md-1 d-flex align-items-end">
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-filter"></i>
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <!-- Contracts Table -->
    <div class="card border-0 shadow-sm">
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-hover mb-0">
                    <thead class="bg-light">
                        <tr>
                            <th>رقم العقد</th>
                            <th>العميل</th>
                            <th>الوحدة</th>
                            <th>القيمة</th>
                            <th>نوع الدفع</th>
                            <th>التقدم</th>
                            <th>الحالة</th>
                            <th>التاريخ</th>
                            <th class="text-center">الإجراءات</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for contract in contracts %}
                        <tr>
                            <td>
                                <a href="{{ url_for('contracts.view', id=contract.id) }}" 
                                   class="text-decoration-none fw-bold">
                                    {{ contract.code }}
                                </a>
                            </td>
                            <td>
                                <div>
                                    <div class="fw-medium">{{ contract.customer.name }}</div>
                                    <small class="text-muted">{{ contract.customer.phone }}</small>
                                </div>
                            </td>
                            <td>
                                <div>
                                    <div>{{ contract.unit.name }}</div>
                                    <small class="text-muted">{{ contract.unit.type }}</small>
                                </div>
                            </td>
                            <td>
                                <div>
                                    <div class="fw-medium">{{ format_currency(contract.final_price) }}</div>
                                    <small class="text-muted">مدفوع: {{ format_currency(contract.paid_amount) }}</small>
                                </div>
                            </td>
                            <td>
                                {% if contract.payment_type == 'cash' %}
                                    <span class="badge bg-success">نقدي</span>
                                {% elif contract.payment_type == 'installment' %}
                                    <span class="badge bg-info">أقساط</span>
                                {% else %}
                                    <span class="badge bg-warning">مختلط</span>
                                {% endif %}
                            </td>
                            <td>
                                <div class="progress" style="height: 20px;">
                                    <div class="progress-bar" role="progressbar" 
                                         style="width: {{ contract.completion_percentage }}%"
                                         aria-valuenow="{{ contract.completion_percentage }}" 
                                         aria-valuemin="0" aria-valuemax="100">
                                        {{ contract.completion_percentage }}%
                                    </div>
                                </div>
                            </td>
                            <td>
                                {% if contract.status == 'active' %}
                                    <span class="badge bg-success">نشط</span>
                                {% elif contract.status == 'draft' %}
                                    <span class="badge bg-secondary">مسودة</span>
                                {% elif contract.status == 'completed' %}
                                    <span class="badge bg-primary">مكتمل</span>
                                {% elif contract.status == 'cancelled' %}
                                    <span class="badge bg-danger">ملغي</span>
                                {% else %}
                                    <span class="badge bg-warning">{{ contract.status }}</span>
                                {% endif %}
                                
                                {% if contract.is_overdue %}
                                    <span class="badge bg-danger ms-1">
                                        <i class="fas fa-exclamation-triangle"></i> متأخر
                                    </span>
                                {% endif %}
                            </td>
                            <td>
                                <small>{{ contract.contract_date.strftime('%Y-%m-%d') }}</small>
                            </td>
                            <td>
                                <div class="btn-group" role="group">
                                    <a href="{{ url_for('contracts.view', id=contract.id) }}" 
                                       class="btn btn-sm btn-outline-primary" title="عرض">
                                        <i class="fas fa-eye"></i>
                                    </a>
                                    <a href="{{ url_for('contracts.edit', id=contract.id) }}" 
                                       class="btn btn-sm btn-outline-warning" title="تعديل">
                                        <i class="fas fa-edit"></i>
                                    </a>
                                    <a href="{{ url_for('installments.contract', contract_id=contract.id) }}" 
                                       class="btn btn-sm btn-outline-info" title="الأقساط">
                                        <i class="fas fa-list"></i>
                                    </a>
                                    <button onclick="printContract('{{ contract.id }}')" 
                                            class="btn btn-sm btn-outline-secondary" title="طباعة">
                                        <i class="fas fa-print"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="9" class="text-center py-5">
                                <img src="/static/img/no-data.svg" alt="No data" style="max-width: 200px;" class="mb-3">
                                <p class="text-muted">لا توجد عقود</p>
                                <a href="{{ url_for('contracts.create') }}" class="btn btn-primary">
                                    <i class="fas fa-plus-circle me-2"></i>إضافة عقد جديد
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        {% if pagination.pages > 1 %}
        <div class="card-footer bg-white">
            <nav aria-label="Page navigation">
                <ul class="pagination justify-content-center mb-0">
                    {% for page in pagination.iter_pages() %}
                        {% if page %}
                            <li class="page-item {% if page == pagination.page %}active{% endif %}">
                                <a class="page-link" href="{{ url_for('contracts.index', page=page, **request.args) }}">
                                    {{ page }}
                                </a>
                            </li>
                        {% else %}
                            <li class="page-item disabled"><span class="page-link">...</span></li>
                        {% endif %}
                    {% endfor %}
                </ul>
            </nav>
        </div>
        {% endif %}
    </div>
</div>

<script>
// تصدير العقود
function exportContracts() {
    const params = new URLSearchParams(window.location.search);
    window.location.href = `{{ url_for('contracts.export') }}?${params.toString()}`;
}

// طباعة العقد
function printContract(contractId) {
    window.open(`{{ url_for('contracts.print', id='') }}${contractId}`, '_blank');
}

// تحديث الفلاتر تلقائياً
document.querySelectorAll('#filterForm select').forEach(select => {
    select.addEventListener('change', () => {
        document.getElementById('filterForm').submit();
    });
});
</script>
{% endblock %}
'''
    
    with open(os.path.join(template_dir, "index.html"), 'w', encoding='utf-8') as f:
        f.write(index_template)
    
    print("  ✅ تم إنشاء قالب قائمة العقود")
    
    # سأكمل بقية القوالب في الرسائل التالية...
    return template_dir

def main():
    """تنفيذ الإصلاح الشامل"""
    print("🚀 بدء الإصلاح الشامل والجذري لنظام العقود والأقساط...\n")
    
    # إنشاء نسخة احتياطية
    backup_dir = create_backup()
    print(f"\n📁 النسخة الاحتياطية محفوظة في: {backup_dir}")
    
    # إنشاء النماذج المحسّنة
    contract_model = create_enhanced_contract_model()
    installment_model = create_enhanced_installment_model()
    
    # إنشاء القوالب
    template_dir = create_contract_templates()
    
    print("\n✅ تم إنشاء الملفات الأساسية بنجاح!")
    print("\n📋 الخطوات التالية:")
    print("1. مراجعة النماذج الجديدة في:")
    print(f"   - {contract_model}")
    print(f"   - {installment_model}")
    print("2. تحديث قاعدة البيانات لاستخدام النماذج الجديدة")
    print("3. إنشاء واجهات المستخدم الكاملة")
    print("4. إضافة وظائف API")
    print("5. إجراء اختبارات شاملة")

if __name__ == '__main__':
    main()