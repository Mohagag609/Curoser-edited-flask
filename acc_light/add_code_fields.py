#!/usr/bin/env python3
"""
Add code field to all entities
"""

import sys
sys.path.insert(0, '/workspace/acc_light')

from app import app
from acc.extensions import db
from acc.models import Customer, Supplier, Contractor, Partner, Broker, Material, Safe, Contract, Unit
from acc.services.code_generator import *
from sqlalchemy import text

def add_code_columns():
    """Add code columns to tables that don't have them"""
    with app.app_context():
        print("Adding code columns to tables...")
        
        with db.engine.connect() as conn:
            # Check and add code column for each table
            tables_to_update = [
                ('customers', 'Customer'),
                ('suppliers', 'Supplier'),
                ('contractors', 'Contractor'),
                ('partners', 'Partner'),
                ('brokers', 'Broker'),
                ('materials', 'Material'),
                ('contracts', 'Contract'),
                ('units', 'Unit')
            ]
            
            for table_name, model_name in tables_to_update:
                try:
                    # Check if column exists
                    result = conn.execute(text(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        AND column_name = 'code'
                    """))
                    
                    if not result.fetchone():
                        print(f"Adding code column to {table_name}...")
                        conn.execute(text(f"""
                            ALTER TABLE {table_name} 
                            ADD COLUMN code VARCHAR(20)
                        """))
                        conn.commit()
                        print(f"✓ Added code column to {table_name}")
                    else:
                        print(f"- Code column already exists in {table_name}")
                        
                except Exception as e:
                    print(f"⚠️  Error with {table_name}: {e}")
                    # For SQLite, columns might already exist
                    pass

def populate_codes():
    """Populate code field for existing records"""
    with app.app_context():
        print("\nPopulating codes for existing records...")
        
        # Customers
        customers = Customer.query.filter(
            db.or_(Customer.code == None, Customer.code == '')
        ).all()
        for i, customer in enumerate(customers):
            customer.code = f"C{str(i+1).zfill(3)}"
        print(f"✓ Updated {len(customers)} customers")
        
        # Suppliers
        suppliers = Supplier.query.filter(
            db.or_(Supplier.code == None, Supplier.code == '')
        ).all()
        for i, supplier in enumerate(suppliers):
            supplier.code = f"S{str(i+1).zfill(3)}"
        print(f"✓ Updated {len(suppliers)} suppliers")
        
        # Contractors
        contractors = Contractor.query.filter(
            db.or_(Contractor.code == None, Contractor.code == '')
        ).all()
        for i, contractor in enumerate(contractors):
            contractor.code = f"CON{str(i+1).zfill(3)}"
        print(f"✓ Updated {len(contractors)} contractors")
        
        # Partners
        partners = Partner.query.filter(
            db.or_(Partner.code == None, Partner.code == '')
        ).all()
        for i, partner in enumerate(partners):
            partner.code = f"P{str(i+1).zfill(3)}"
        print(f"✓ Updated {len(partners)} partners")
        
        # Brokers
        brokers = Broker.query.filter(
            db.or_(Broker.code == None, Broker.code == '')
        ).all()
        for i, broker in enumerate(brokers):
            broker.code = f"B{str(i+1).zfill(3)}"
        print(f"✓ Updated {len(brokers)} brokers")
        
        # Materials
        materials = Material.query.filter(
            db.or_(Material.code == None, Material.code == '')
        ).all()
        for i, material in enumerate(materials):
            material.code = f"M{str(i+1).zfill(3)}"
        print(f"✓ Updated {len(materials)} materials")
        
        # Contracts
        contracts = Contract.query.filter(
            db.or_(Contract.code == None, Contract.code == '')
        ).all()
        for i, contract in enumerate(contracts):
            contract.code = f"CNT{str(i+1).zfill(3)}"
        print(f"✓ Updated {len(contracts)} contracts")
        
        # Units - generate from building/floor/name
        units = Unit.query.filter(
            db.or_(Unit.code == None, Unit.code == '')
        ).all()
        for unit in units:
            if unit.building and unit.floor and unit.name:
                unit.code = generate_unit_code(unit.building, unit.floor, unit.name)
            else:
                unit.code = f"U{unit.id[:6]}"
        print(f"✓ Updated {len(units)} units")
        
        # Commit all changes
        try:
            db.session.commit()
            print("\n✅ All codes populated successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error committing changes: {e}")

if __name__ == '__main__':
    add_code_columns()
    populate_codes()