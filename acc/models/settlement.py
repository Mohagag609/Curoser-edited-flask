from acc.extensions import db
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime, Boolean, func
from datetime import datetime


class Phase(db.Model):
    """مراحل المشروع"""
    __tablename__ = 'phases'
    
    id = Column(String(20), primary_key=True)
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    settled_at = Column(DateTime)  # تاريخ التسوية
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    project = db.relationship('Project', backref='phases')
    expenses = db.relationship('Expense', backref='phase', lazy='dynamic', cascade='all, delete-orphan')
    material_issues = db.relationship('MaterialIssue', backref='phase', lazy='dynamic', cascade='all, delete-orphan')
    settlements = db.relationship('PhaseSettlement', backref='phase', lazy='dynamic', cascade='all, delete-orphan')
    # partner_groups relationship is defined in PhasePartnerGroup model
    
    @property
    def is_settled(self):
        """هل المرحلة متسوية؟"""
        return self.settled_at is not None
    
    def total_expenses(self):
        """إجمالي المصروفات"""
        expenses_sum = db.session.query(func.sum(Expense.amount)).filter_by(phase_id=self.id).scalar() or 0
        return float(expenses_sum)
    
    def total_materials(self):
        """إجمالي قيمة المواد المصروفة"""
        materials_sum = db.session.query(
            func.sum(MaterialIssue.quantity * MaterialIssue.unit_cost)
        ).filter_by(phase_id=self.id).scalar() or 0
        return float(materials_sum)
    
    def total_cost(self):
        """إجمالي التكلفة (مصروفات + مواد)"""
        return self.total_expenses() + self.total_materials()
    
    def __repr__(self):
        return f'<Phase {self.name}>'


class PhasePartnerGroup(db.Model):
    """مجموعات الشركاء في المراحل"""
    __tablename__ = 'phase_partner_groups'
    
    id = Column(String(20), primary_key=True)
    phase_id = Column(String(20), ForeignKey('phases.id'), nullable=False)
    name = Column(String(200), nullable=False)  # اسم المجموعة
    share_percentage = Column(Numeric(5, 2), default=0)  # نسبة المجموعة في المرحلة
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    phase = db.relationship('Phase', backref=db.backref('partner_groups', lazy='dynamic'))
    members = db.relationship('PhasePartner', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PhasePartnerGroup {self.name} in phase {self.phase_id}>'


class PhasePartner(db.Model):
    """شركاء المراحل (أعضاء المجموعات)"""
    __tablename__ = 'phase_partners'
    
    id = Column(String(20), primary_key=True)
    group_id = Column(String(20), ForeignKey('phase_partner_groups.id'), nullable=False)
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False)
    share_percentage = Column(Numeric(5, 2), default=0)  # نسبة الشريك داخل المجموعة
    joined_at = Column(DateTime, default=func.now())
    left_at = Column(DateTime)  # تاريخ الخروج من المجموعة
    is_active = Column(Boolean, default=True)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('group_id', 'partner_id', name='_phase_partner_uc'),
    )
    
    # Relationships
    partner = db.relationship('Partner', backref='phase_partnerships')
    
    def __repr__(self):
        return f'<PhasePartner {self.partner_id} in group {self.group_id}>'


class ProjectPartner(db.Model):
    """شركاء المشاريع (للتوافق مع الكود القديم)"""
    __tablename__ = 'project_partners'
    
    id = Column(String(20), primary_key=True)
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False)
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False)
    share_percentage = Column(Numeric(5, 2), default=0)
    joined_at = Column(DateTime, default=func.now())
    left_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('project_id', 'partner_id', name='_project_partner_uc'),
    )
    
    # Relationships
    project = db.relationship('Project', backref='project_partners')
    partner = db.relationship('Partner', backref='project_partnerships')
    
    def __repr__(self):
        return f'<ProjectPartner {self.partner_id} in {self.project_id}>'


class Expense(db.Model):
    """مصروفات المرحلة"""
    __tablename__ = 'expenses'
    
    id = Column(String(20), primary_key=True)
    phase_id = Column(String(20), ForeignKey('phases.id'), nullable=False)
    paid_by_partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    expense_date = Column(DateTime, default=func.now())
    category = Column(String(100))
    description = Column(Text)
    receipt_number = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    paid_by = db.relationship('Partner', foreign_keys=[paid_by_partner_id])
    
    def __repr__(self):
        return f'<Expense {self.amount} by {self.paid_by_partner_id}>'


class MaterialIssue(db.Model):
    """صرف مواد للمرحلة"""
    __tablename__ = 'material_issues'
    
    id = Column(String(20), primary_key=True)
    phase_id = Column(String(20), ForeignKey('phases.id'), nullable=False)
    material_id = Column(String(20), ForeignKey('materials.id'), nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_cost = Column(Numeric(15, 2), nullable=False)
    issue_date = Column(DateTime, default=func.now())
    issued_by_partner_id = Column(String(20), ForeignKey('partners.id'))
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    material = db.relationship('Material', backref='issues')
    issued_by = db.relationship('Partner', foreign_keys=[issued_by_partner_id])
    
    @property
    def total_cost(self):
        """إجمالي قيمة المواد المصروفة"""
        return float(self.quantity * self.unit_cost)
    
    def __repr__(self):
        return f'<MaterialIssue {self.quantity} of {self.material_id}>'


class PartnerLedger(db.Model):
    """دفتر أرصدة الشركاء في المشروع"""
    __tablename__ = 'partner_ledgers'
    
    id = Column(String(20), primary_key=True)
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False)
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False)
    balance = Column(Numeric(15, 2), default=0)  # موجب = عليه، سالب = له
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('project_id', 'partner_id', name='_project_partner_ledger_uc'),
    )
    
    # Relationships
    partner = db.relationship('Partner', foreign_keys=[partner_id])
    
    def __repr__(self):
        return f'<PartnerLedger {self.partner_id}: {self.balance}>'


class PhaseSettlement(db.Model):
    """تسوية المرحلة"""
    __tablename__ = 'phase_settlements'
    
    id = Column(String(20), primary_key=True)
    phase_id = Column(String(20), ForeignKey('phases.id'), nullable=False)
    settlement_date = Column(DateTime, default=func.now())
    total_expenses = Column(Numeric(15, 2), nullable=False)
    total_materials = Column(Numeric(15, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    partners_count = Column(Integer, nullable=False)
    average_per_partner = Column(Numeric(15, 2), nullable=False)
    notes = Column(Text)
    created_by = Column(String(100))  # اسم المستخدم
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    lines = db.relationship('PhaseSettlementLine', backref='settlement', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PhaseSettlement {self.phase_id} at {self.settlement_date}>'


class PhaseSettlementLine(db.Model):
    """تفاصيل تسوية كل شريك"""
    __tablename__ = 'phase_settlement_lines'
    
    id = Column(String(20), primary_key=True)
    settlement_id = Column(String(20), ForeignKey('phase_settlements.id'), nullable=False)
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)  # ما دفعه الشريك
    average_amount = Column(Numeric(15, 2), nullable=False)  # المتوسط
    difference = Column(Numeric(15, 2), nullable=False)  # الفرق (موجب = عليه، سالب = له)
    previous_balance = Column(Numeric(15, 2), default=0)  # الرصيد السابق
    new_balance = Column(Numeric(15, 2), default=0)  # الرصيد الجديد
    
    # Relationships
    partner = db.relationship('Partner', foreign_keys=[partner_id])
    
    def __repr__(self):
        return f'<PhaseSettlementLine {self.partner_id}: {self.difference}>'