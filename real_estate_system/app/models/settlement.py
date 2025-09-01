from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, Date, Boolean, index
from sqlalchemy.orm import relationship


class Phase(BaseModel):
    """مرحلة المشروع"""
    __tablename__ = 'phases'
    
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    settled_at = Column(Date)
    status = Column(String(20), default='نشط', index=True)
    
    # Relationships
    project = relationship('Project', backref='phase_projects')
    expenses = relationship('Expense', backref='phase', lazy='dynamic', cascade='all, delete-orphan')
    material_issues = relationship('MaterialIssue', backref='phase', lazy='dynamic', cascade='all, delete-orphan')
    settlements = relationship('PhaseSettlement', backref='phase', lazy='dynamic', cascade='all, delete-orphan')
    phase_partners = relationship('PhasePartner', backref='phase', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Phase {self.name}>'
    
    @property
    def is_settled(self):
        """هل المرحلة متسوية؟"""
        return self.settled_at is not None
    
    @property
    def total_expenses(self):
        """إجمالي المصروفات"""
        from sqlalchemy import func
        result = db.session.query(func.sum(Expense.amount)).filter_by(phase_id=self.id).scalar()
        return float(result) if result else 0.0
    
    @property
    def total_materials(self):
        """إجمالي قيمة المواد المصروفة"""
        from sqlalchemy import func
        result = db.session.query(
            func.sum(MaterialIssue.quantity * MaterialIssue.unit_cost)
        ).filter_by(phase_id=self.id).scalar()
        return float(result) if result else 0.0
    
    @property
    def total_cost(self):
        """إجمالي التكلفة (مصروفات + مواد)"""
        return self.total_expenses + self.total_materials
    
    def to_dict(self):
        """تحويل المرحلة إلى قاموس"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'settled_at': self.settled_at.isoformat() if self.settled_at else None,
            'status': self.status,
            'is_settled': self.is_settled,
            'total_expenses': self.total_expenses,
            'total_materials': self.total_materials,
            'total_cost': self.total_cost,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ProjectPartner(BaseModel):
    """شريك في المشروع"""
    __tablename__ = 'project_partners'
    
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False, index=True)
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False, index=True)
    percentage = Column(Numeric(5, 2), nullable=False)
    role = Column(String(100))
    
    def __repr__(self):
        return f'<ProjectPartner {self.partner.name} - {self.percentage}%>'


class PhasePartner(BaseModel):
    """شريك في المرحلة"""
    __tablename__ = 'phase_partners'
    
    phase_id = Column(String(20), ForeignKey('phases.id'), nullable=False, index=True)
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False, index=True)
    percentage = Column(Numeric(5, 2), nullable=False)
    role = Column(String(100))
    
    def __repr__(self):
        return f'<PhasePartner {self.partner.name} - {self.percentage}%>'


class PhasePartnerGroup(BaseModel):
    """مجموعة شركاء في المرحلة"""
    __tablename__ = 'phase_partner_groups'
    
    phase_id = Column(String(20), ForeignKey('phases.id'), nullable=False, index=True)
    group_id = Column(String(20), ForeignKey('partner_groups.id'), nullable=False, index=True)
    percentage = Column(Numeric(5, 2), nullable=False)
    
    def __repr__(self):
        return f'<PhasePartnerGroup {self.group.name} - {self.percentage}%>'


class Expense(BaseModel):
    """مصروف"""
    __tablename__ = 'expenses'
    
    phase_id = Column(String(20), ForeignKey('phases.id'), nullable=False, index=True)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    expense_date = Column(Date, nullable=False)
    category = Column(String(100), index=True)
    reference = Column(String(100))
    
    def __repr__(self):
        return f'<Expense {self.description} - {self.amount}>'


class MaterialIssue(BaseModel):
    """صرف مادة"""
    __tablename__ = 'material_issues'
    
    phase_id = Column(String(20), ForeignKey('phases.id'), nullable=False, index=True)
    material_id = Column(String(20), ForeignKey('materials.id'), nullable=False, index=True)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    issue_date = Column(Date, nullable=False)
    reference = Column(String(100))
    
    # Relationships
    material = relationship('Material', backref='material_issues')
    
    def __repr__(self):
        return f'<MaterialIssue {self.material.name} - {self.quantity}>'
    
    @property
    def total_cost(self):
        """إجمالي التكلفة"""
        return float(self.quantity * self.unit_cost)


class PartnerLedger(BaseModel):
    """دفتر الشريك"""
    __tablename__ = 'partner_ledgers'
    
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False, index=True)
    phase_id = Column(String(20), ForeignKey('phases.id'), nullable=False, index=True)
    debit_amount = Column(Numeric(15, 2), default=0)
    credit_amount = Column(Numeric(15, 2), default=0)
    balance = Column(Numeric(15, 2), default=0)
    description = Column(Text)
    reference = Column(String(100))
    
    def __repr__(self):
        return f'<PartnerLedger {self.partner.name} - {self.balance}>'


class PhaseSettlement(BaseModel):
    """تسوية المرحلة"""
    __tablename__ = 'phase_settlements'
    
    phase_id = Column(String(20), ForeignKey('phases.id'), nullable=False, index=True)
    settlement_date = Column(Date, nullable=False)
    total_cost = Column(Numeric(15, 2), nullable=False)
    total_income = Column(Numeric(15, 2), nullable=False)
    net_profit = Column(Numeric(15, 2), nullable=False)
    status = Column(String(20), default='مكتمل', index=True)
    
    # Relationships
    settlement_lines = relationship('PhaseSettlementLine', backref='settlement', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PhaseSettlement {self.phase.name} - {self.settlement_date}>'


class PhaseSettlementLine(BaseModel):
    """سطر تسوية المرحلة"""
    __tablename__ = 'phase_settlement_lines'
    
    settlement_id = Column(String(20), ForeignKey('phase_settlements.id'), nullable=False, index=True)
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False, index=True)
    percentage = Column(Numeric(5, 2), nullable=False)
    share_amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    remaining_amount = Column(Numeric(15, 2), default=0)
    
    def __repr__(self):
        return f'<PhaseSettlementLine {self.partner.name} - {self.share_amount}>'