from acc.extensions import db
from sqlalchemy import Column, Integer, String, Float, Numeric, ForeignKey, Date, Text, DateTime, func


class Material(db.Model):
    __tablename__ = 'materials'
    
    id = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True)
    unit = Column(String(50))  # متر، كيلو، قطعة
    unit_cost = Column(Numeric(15, 2), default=0)  # سعر الوحدة الافتراضي
    category = Column(String(100))
    description = Column(Text)
    min_stock = Column(Float, default=0)
    current_stock = Column(Float, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    project_uses = db.relationship('ProjectMaterial', backref='material', lazy='dynamic')
    
    def __repr__(self):
        return f'<Material {self.code} - {self.name}>'


class ProjectMaterial(db.Model):
    __tablename__ = 'project_materials'
    
    id = Column(String(20), primary_key=True)
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False)
    material_id = Column(String(20), ForeignKey('materials.id'), nullable=False)
    supplier_id = Column(String(20), ForeignKey('suppliers.id'))
    quantity = Column(Float, nullable=False)
    unit_price = Column(Numeric(15, 2))
    total_price = Column(Numeric(15, 2))
    purchase_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f'<ProjectMaterial {self.project_id} - {self.material_id}>'