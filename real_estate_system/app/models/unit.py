from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, Boolean, index
from sqlalchemy.orm import relationship


class Unit(BaseModel):
    """نموذج الوحدة"""
    __tablename__ = 'units'
    
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    unit_type = Column(String(50), index=True)  # شقة، فيلا، محل، إلخ
    floor = Column(String(20))
    area = Column(Numeric(10, 2))  # المساحة بالمتر المربع
    price = Column(Numeric(15, 2), nullable=False)
    status = Column(String(50), default='متاح', index=True)  # متاح، محجوز، مباع
    description = Column(Text)
    features = Column(Text)  # المميزات
    is_penthouse = Column(Boolean, default=False)
    is_ground_floor = Column(Boolean, default=False)
    has_balcony = Column(Boolean, default=False)
    has_garden = Column(Boolean, default=False)
    has_parking = Column(Boolean, default=False)
    has_elevator = Column(Boolean, default=False)
    
    # Relationships
    project = relationship('Project', backref='project_units')
    contracts = relationship('Contract', backref='unit', lazy='dynamic', cascade='all, delete-orphan')
    unit_partners = relationship('UnitPartner', backref='unit', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Unit {self.name} - {self.code}>'
    
    @property
    def is_available(self):
        """هل الوحدة متاحة؟"""
        return self.status == 'متاح'
    
    @property
    def is_sold(self):
        """هل الوحدة مباعة؟"""
        return self.status == 'مباع'
    
    @property
    def is_reserved(self):
        """هل الوحدة محجوزة؟"""
        return self.status == 'محجوز'
    
    @property
    def total_contracts(self):
        """إجمالي عدد العقود"""
        return self.contracts.count()
    
    @property
    def active_contract(self):
        """العقد النشط"""
        return self.contracts.filter_by(status='نشط').first()
    
    @property
    def price_per_sqm(self):
        """السعر للمتر المربع"""
        if self.area and self.area > 0:
            return round(float(self.price / self.area), 2)
        return 0
    
    def get_contracts_by_status(self, status):
        """الحصول على العقود حسب الحالة"""
        return self.contracts.filter_by(status=status).all()
    
    def get_partners(self):
        """الحصول على الشركاء"""
        return [up.partner for up in self.unit_partners]
    
    def add_partner(self, partner, percentage):
        """إضافة شريك للوحدة"""
        from app.models.partner import UnitPartner
        unit_partner = UnitPartner(
            unit_id=self.id,
            partner_id=partner.id,
            percentage=percentage
        )
        unit_partner.save()
        return unit_partner
    
    def remove_partner(self, partner):
        """إزالة شريك من الوحدة"""
        unit_partner = self.unit_partners.filter_by(partner_id=partner.id).first()
        if unit_partner:
            unit_partner.delete()
            return True
        return False
    
    def to_dict(self):
        """تحويل الوحدة إلى قاموس"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'code': self.code,
            'name': self.name,
            'unit_type': self.unit_type,
            'floor': self.floor,
            'area': float(self.area) if self.area else None,
            'price': float(self.price) if self.price else 0,
            'status': self.status,
            'description': self.description,
            'features': self.features,
            'is_penthouse': self.is_penthouse,
            'is_ground_floor': self.is_ground_floor,
            'has_balcony': self.has_balcony,
            'has_garden': self.has_garden,
            'has_parking': self.has_parking,
            'has_elevator': self.has_elevator,
            'price_per_sqm': self.price_per_sqm,
            'total_contracts': self.total_contracts,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }