from acc.extensions import db
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, ForeignKey, DateTime, func


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    project_type = Column(String(20), default='عقاري')  # عقاري أو محاسبي
    location = Column(String(200))  # الموقع
    area = Column(String(100))  # المساحة
    contractor_id = Column(String(20), ForeignKey('contractors.id'))  # المقاول الرئيسي
    start_date = Column(Date)
    expected_end_date = Column(Date)
    actual_end_date = Column(Date)
    status = Column(String(50), default='نشط')
    is_default = Column(db.Boolean, default=False)
    budget = Column(Numeric(15, 2))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    contractor = db.relationship('Contractor', foreign_keys=[contractor_id], backref='projects')
    units = db.relationship('Unit', backref='project', lazy='dynamic')
    contracts = db.relationship('Contract', back_populates='project', lazy='dynamic')
    safes = db.relationship('Safe', backref='project', lazy='dynamic')
    vouchers = db.relationship('Voucher', backref='project', lazy='dynamic')
    stages = db.relationship('ProjectStage', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    materials = db.relationship('ProjectMaterial', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    # partners relationship removed - now using phase_partners through phases
    
    def has_feature(self, feature):
        """التحقق من توفر ميزة معينة حسب نوع المشروع"""
        if self.project_type == 'عقاري':
            return True  # كل الميزات متاحة
        elif self.project_type == 'محاسبي':
            # الميزات غير المتاحة في المشاريع المحاسبية
            restricted_features = ['units', 'contracts', 'installments']
            return feature not in restricted_features
        return True
    
    def __repr__(self):
        return f'<Project {self.code} - {self.name}>'
    
    def calculate_total_cost(self):
        """Calculate total cost from stages and materials"""
        stages_cost = db.session.query(func.sum(ProjectStage.cost)).filter_by(project_id=self.id).scalar() or 0
        # Import here to avoid circular import
        from acc.models.material import ProjectMaterial
        materials_cost = db.session.query(func.sum(ProjectMaterial.total_price)).filter_by(project_id=self.id).scalar() or 0
        return stages_cost + materials_cost


class ProjectStage(db.Model):
    __tablename__ = 'project_stages'
    
    id = Column(String(20), primary_key=True)
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False)
    contractor_id = Column(String(20), ForeignKey('contractors.id'))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    cost = Column(Numeric(15, 2))
    status = Column(String(50), default='pending')
    completion_percentage = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    contractor = db.relationship('Contractor', foreign_keys=[contractor_id], backref='stages')
    
    def __repr__(self):
        return f'<ProjectStage {self.name}>'