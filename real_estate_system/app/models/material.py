from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, index
from sqlalchemy.orm import relationship


class Material(BaseModel):
    """نموذج المادة"""
    __tablename__ = 'materials'
    
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    unit = Column(String(50), nullable=False)  # وحدة القياس
    unit_cost = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default='نشط', index=True)
    notes = Column(Text)
    category = Column(String(100), index=True)
    supplier_id = Column(String(20), ForeignKey('suppliers.id'), nullable=True, index=True)
    
    # Relationships
    supplier = relationship('Supplier', backref='materials')
    project_materials = relationship('ProjectMaterial', backref='material', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Material {self.name}>'
    
    @property
    def total_quantity_used(self):
        """إجمالي الكمية المستخدمة"""
        from sqlalchemy import func
        result = db.session.query(func.sum(ProjectMaterial.quantity)).filter_by(material_id=self.id).scalar()
        return float(result) if result else 0.0
    
    @property
    def total_cost_used(self):
        """إجمالي التكلفة المستخدمة"""
        return self.total_quantity_used * float(self.unit_cost)
    
    def to_dict(self):
        """تحويل المادة إلى قاموس"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'unit': self.unit,
            'unit_cost': float(self.unit_cost) if self.unit_cost else 0,
            'status': self.status,
            'notes': self.notes,
            'category': self.category,
            'supplier_id': self.supplier_id,
            'total_quantity_used': self.total_quantity_used,
            'total_cost_used': self.total_cost_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ProjectMaterial(BaseModel):
    """مادة في مشروع"""
    __tablename__ = 'project_materials'
    
    project_id = Column(String(20), ForeignKey('projects.id'), nullable=False, index=True)
    material_id = Column(String(20), ForeignKey('materials.id'), nullable=False, index=True)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(15, 2), nullable=False)
    notes = Column(Text)
    
    def __repr__(self):
        return f'<ProjectMaterial {self.material.name} - {self.quantity}>'
    
    def to_dict(self):
        """تحويل مادة المشروع إلى قاموس"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'material_id': self.material_id,
            'quantity': float(self.quantity) if self.quantity else 0,
            'unit_cost': float(self.unit_cost) if self.unit_cost else 0,
            'total_cost': float(self.total_cost) if self.total_cost else 0,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }