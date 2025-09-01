from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, Boolean, index
from sqlalchemy.orm import relationship


class Partner(BaseModel):
    """نموذج الشريك"""
    __tablename__ = 'partners'
    
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    phone = Column(String(20), index=True)
    national_id = Column(String(20), index=True)
    address = Column(Text)
    email = Column(String(100), index=True)
    status = Column(String(20), default='نشط', index=True)
    notes = Column(Text)
    is_company = Column(Boolean, default=False)
    company_registration = Column(String(50))
    tax_number = Column(String(50))
    
    # Relationships
    unit_partners = relationship('UnitPartner', backref='partner', lazy='dynamic', cascade='all, delete-orphan')
    partner_debts = relationship('PartnerDebt', backref='partner', lazy='dynamic', cascade='all, delete-orphan')
    group_memberships = relationship('PartnerGroupMember', backref='partner', lazy='dynamic', cascade='all, delete-orphan')
    project_partners = relationship('ProjectPartner', backref='partner', lazy='dynamic', cascade='all, delete-orphan')
    phase_partners = relationship('PhasePartner', backref='partner', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Partner {self.name}>'
    
    @property
    def total_units(self):
        """إجمالي عدد الوحدات"""
        return self.unit_partners.count()
    
    @property
    def total_investment(self):
        """إجمالي الاستثمار"""
        from sqlalchemy import func
        result = db.session.query(func.sum(UnitPartner.percentage * Unit.price / 100)).join(
            Unit, UnitPartner.unit_id == Unit.id
        ).filter(UnitPartner.partner_id == self.id).scalar()
        return float(result) if result else 0.0
    
    @property
    def total_debt(self):
        """إجمالي الدين"""
        from sqlalchemy import func
        result = db.session.query(func.sum(PartnerDebt.amount)).filter_by(partner_id=self.id).scalar()
        return float(result) if result else 0.0
    
    @property
    def total_paid(self):
        """إجمالي المدفوع"""
        from sqlalchemy import func
        result = db.session.query(func.sum(PartnerDebt.amount)).filter_by(
            partner_id=self.id,
            status='مدفوع'
        ).scalar()
        return float(result) if result else 0.0
    
    @property
    def remaining_debt(self):
        """الدين المتبقي"""
        return self.total_debt - self.total_paid
    
    def get_units(self):
        """الحصول على الوحدات"""
        return [up.unit for up in self.unit_partners]
    
    def get_groups(self):
        """الحصول على المجموعات"""
        return [gm.group for gm in self.group_memberships]
    
    def add_to_unit(self, unit, percentage):
        """إضافة الشريك لوحدة"""
        from app.models.unit import UnitPartner
        unit_partner = UnitPartner(
            unit_id=unit.id,
            partner_id=self.id,
            percentage=percentage
        )
        unit_partner.save()
        return unit_partner
    
    def remove_from_unit(self, unit):
        """إزالة الشريك من وحدة"""
        unit_partner = self.unit_partners.filter_by(unit_id=unit.id).first()
        if unit_partner:
            unit_partner.delete()
            return True
        return False
    
    def add_debt(self, amount, description=None):
        """إضافة دين"""
        from app.models.partner import PartnerDebt
        debt = PartnerDebt(
            partner_id=self.id,
            amount=amount,
            description=description
        )
        debt.save()
        return debt
    
    def to_dict(self):
        """تحويل الشريك إلى قاموس"""
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
            'is_company': self.is_company,
            'company_registration': self.company_registration,
            'tax_number': self.tax_number,
            'total_units': self.total_units,
            'total_investment': self.total_investment,
            'total_debt': self.total_debt,
            'total_paid': self.total_paid,
            'remaining_debt': self.remaining_debt,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PartnerGroup(BaseModel):
    """مجموعة الشركاء"""
    __tablename__ = 'partner_groups'
    
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    status = Column(String(20), default='نشط', index=True)
    
    # Relationships
    members = relationship('PartnerGroupMember', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PartnerGroup {self.name}>'
    
    @property
    def total_members(self):
        """إجمالي عدد الأعضاء"""
        return self.members.count()
    
    def add_member(self, partner, role='عضو'):
        """إضافة عضو للمجموعة"""
        member = PartnerGroupMember(
            group_id=self.id,
            partner_id=partner.id,
            role=role
        )
        member.save()
        return member
    
    def remove_member(self, partner):
        """إزالة عضو من المجموعة"""
        member = self.members.filter_by(partner_id=partner.id).first()
        if member:
            member.delete()
            return True
        return False


class PartnerGroupMember(BaseModel):
    """عضو في مجموعة الشركاء"""
    __tablename__ = 'partner_group_members'
    
    group_id = Column(String(20), ForeignKey('partner_groups.id'), nullable=False, index=True)
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False, index=True)
    role = Column(String(50), default='عضو')
    
    def __repr__(self):
        return f'<PartnerGroupMember {self.partner.name} in {self.group.name}>'


class UnitPartner(BaseModel):
    """شريك في وحدة"""
    __tablename__ = 'unit_partners'
    
    unit_id = Column(String(20), ForeignKey('units.id'), nullable=False, index=True)
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False, index=True)
    percentage = Column(Numeric(5, 2), nullable=False)
    
    def __repr__(self):
        return f'<UnitPartner {self.partner.name} - {self.percentage}%>'


class PartnerDebt(BaseModel):
    """دين الشريك"""
    __tablename__ = 'partner_debts'
    
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text)
    status = Column(String(20), default='معلق', index=True)  # معلق، مدفوع
    payment_date = Column(Date)
    payment_method = Column(String(50))
    payment_reference = Column(String(100))
    
    def __repr__(self):
        return f'<PartnerDebt {self.partner.name} - {self.amount}>'
    
    @property
    def is_paid(self):
        """هل الدين مدفوع؟"""
        return self.status == 'مدفوع'
    
    def mark_as_paid(self, payment_date=None, payment_method=None, payment_reference=None):
        """تسجيل الدين كمدفوع"""
        from datetime import date
        self.status = 'مدفوع'
        self.payment_date = payment_date or date.today()
        self.payment_method = payment_method
        self.payment_reference = payment_reference
        self.save()