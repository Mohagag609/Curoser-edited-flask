from acc.extensions import db
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, DateTime, func, UniqueConstraint


class Partner(db.Model):
    __tablename__ = 'partners'
    
    id = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    phone = Column(String(20))
    national_id = Column(String(20), unique=True)
    address = Column(db.Text)
    notes = Column(db.Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    unit_partners = db.relationship('UnitPartner', backref='partner', lazy='dynamic')
    group_memberships = db.relationship('PartnerGroupMember', backref='partner', lazy='dynamic')
    debts_owed = db.relationship('PartnerDebt', foreign_keys='PartnerDebt.creditor_id', 
                                  backref='creditor', lazy='dynamic')
    debts_due = db.relationship('PartnerDebt', foreign_keys='PartnerDebt.debtor_id', 
                                   backref='debtor', lazy='dynamic')
    # phase_partnerships relationship is defined in PhasePartner model
    
    def __repr__(self):
        return f'<Partner {self.name}>'


class PartnerGroup(db.Model):
    __tablename__ = 'partner_groups'
    
    id = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    notes = Column(db.Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    members = db.relationship('PartnerGroupMember', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_total_percentage(self):
        return sum(member.percentage for member in self.members)


class PartnerGroupMember(db.Model):
    __tablename__ = 'partner_group_members'
    
    id = Column(String(20), primary_key=True)
    group_id = Column(String(20), ForeignKey('partner_groups.id'), nullable=False)
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False)
    percentage = Column(Numeric(5, 2), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('group_id', 'partner_id', name='_group_partner_uc'),
    )


class UnitPartner(db.Model):
    __tablename__ = 'unit_partners'
    
    id = Column(String(20), primary_key=True)
    unit_id = Column(String(20), ForeignKey('units.id'), nullable=False)
    partner_id = Column(String(20), ForeignKey('partners.id'), nullable=False)
    percentage = Column(Numeric(5, 2), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        UniqueConstraint('unit_id', 'partner_id', name='_unit_partner_uc'),
    )


class PartnerDebt(db.Model):
    __tablename__ = 'partner_debts'
    
    id = Column(String(20), primary_key=True)
    creditor_id = Column(String(20), ForeignKey('partners.id'), nullable=False)
    debtor_id = Column(String(20), ForeignKey('partners.id'), nullable=False)
    unit_id = Column(String(20), ForeignKey('units.id'))
    amount = Column(Numeric(15, 2), nullable=False)
    remaining_amount = Column(Numeric(15, 2), nullable=False)
    description = Column(db.Text)
    status = Column(String(20), default='نشط')
    created_at = Column(DateTime, default=func.now())