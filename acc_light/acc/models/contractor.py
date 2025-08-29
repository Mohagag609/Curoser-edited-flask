from acc.extensions import db
from sqlalchemy import Column, Integer, String, Text, DateTime, func


class Contractor(db.Model):
    __tablename__ = 'contractors'
    
    id = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    specialty = Column(String(100))
    address = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    # project_stages relationship is handled by ProjectStage model
    
    def __repr__(self):
        return f'<Contractor {self.name}>'