from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Text, Date, Numeric, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship


class Project(BaseModel):
    """نموذج المشروع"""
    __tablename__ = 'projects'
    
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    project_type = Column(String(20), default='عقاري', index=True)  # عقاري أو محاسبي
    location = Column(String(200))
    area = Column(String(100))
    contractor_id = Column(String(20), ForeignKey('contractors.id'), index=True)
    start_date = Column(Date)
    expected_end_date = Column(Date)
    actual_end_date = Column(Date)
    status = Column(String(50), default='نشط', index=True)
    is_default = Column(Boolean, default=False)
    budget = Column(Numeric(15, 2))
    
    # Relationships
    contractor = relationship('Contractor', foreign_keys=[contractor_id], backref='projects')
    units = relationship('Unit', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    contracts = relationship('Contract', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    safes = relationship('Safe', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    vouchers = relationship('Voucher', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    phases = relationship('Phase', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    project_partners = relationship('ProjectPartner', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    project_materials = relationship('ProjectMaterial', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Project {self.name}>'
    
    @property
    def total_units(self):
        """إجمالي عدد الوحدات"""
        return self.units.count()
    
    @property
    def sold_units(self):
        """عدد الوحدات المباعة"""
        return self.units.filter_by(status='مباع').count()
    
    @property
    def available_units(self):
        """عدد الوحدات المتاحة"""
        return self.units.filter_by(status='متاح').count()
    
    @property
    def total_contracts_value(self):
        """إجمالي قيمة العقود"""
        from sqlalchemy import func
        result = db.session.query(func.sum(Contract.total_price)).filter_by(project_id=self.id).scalar()
        return float(result) if result else 0.0
    
    @property
    def completion_percentage(self):
        """نسبة الإنجاز"""
        if self.total_units == 0:
            return 0
        return round((self.sold_units / self.total_units) * 100, 2)
    
    def get_units_by_status(self, status):
        """الحصول على الوحدات حسب الحالة"""
        return self.units.filter_by(status=status).all()
    
    def get_contracts_by_status(self, status):
        """الحصول على العقود حسب الحالة"""
        return self.contracts.filter_by(status=status).all()


class ProjectStage(BaseModel):
    """مراحل المشروع"""
    __tablename__ = 'project_stages'
    
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(50), default='مخطط')
    progress_percentage = Column(Numeric(5, 2), default=0)
    
    # Relationships
    project = relationship('Project', backref='stages')
    
    def __repr__(self):
        return f'<ProjectStage {self.name}>'