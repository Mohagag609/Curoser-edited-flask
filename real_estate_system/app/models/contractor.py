from app import db
from app.models.base import BaseModel
from sqlalchemy import Column, String, Text, index


class Contractor(BaseModel):
    """نموذج المقاول"""
    __tablename__ = 'contractors'
    
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    phone = Column(String(20), index=True)
    national_id = Column(String(20), index=True)
    address = Column(Text)
    email = Column(String(100), index=True)
    status = Column(String(20), default='نشط', index=True)
    notes = Column(Text)
    contact_person = Column(String(200))
    license_number = Column(String(50))
    specialization = Column(String(200))
    
    def __repr__(self):
        return f'<Contractor {self.name}>'
    
    @property
    def total_projects(self):
        """إجمالي عدد المشاريع"""
        return len(self.projects)
    
    def to_dict(self):
        """تحويل المقاول إلى قاموس"""
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
            'contact_person': self.contact_person,
            'license_number': self.license_number,
            'specialization': self.specialization,
            'total_projects': self.total_projects,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }