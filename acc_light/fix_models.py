#!/usr/bin/env python3
"""Fix model relationships for production."""

from app import app
from acc.extensions import db
from acc.models import Contract, Customer, Unit

with app.app_context():
    print("Fixing model relationships...")
    
    # Add explicit relationships
    if not hasattr(Contract, 'customer_rel'):
        Contract.customer_rel = db.relationship('Customer', foreign_keys=[Contract.customer_id], backref='contract_list')
    
    if not hasattr(Contract, 'unit_rel'):
        Contract.unit_rel = db.relationship('Unit', foreign_keys=[Contract.unit_id], backref='contract_list')
    
    print("Model relationships fixed!")