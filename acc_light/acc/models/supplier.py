from acc.extensions import db
from sqlalchemy import Column, Integer, String, Text, DateTime, func


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    project_materials = db.relationship('ProjectMaterial', backref='supplier', lazy='dynamic')
    
    def __repr__(self):
        return f'<Supplier {self.name}>'