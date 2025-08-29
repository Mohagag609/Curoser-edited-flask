#!/usr/bin/env python3
from app import app, db
from acc.models import *
from acc.services.utils import generate_uid
from datetime import datetime, timedelta

with app.app_context():
    # Check if data exists
    if Project.query.count() > 0:
        print("Database already has data.")
        exit()
    
    print("Seeding basic data...")
    
    # Add a default project
    project = Project(
        id=generate_uid('PRJ'),
        name='مشروع افتراضي',
        code='DEFAULT',
        status='نشط',
        is_default=True
    )
    db.session.add(project)
    db.session.commit()
    
    # Add a customer
    customer = Customer(
        id=generate_uid('C'),
        name='عميل افتراضي',
        phone='01000000000',
        status='نشط'
    )
    db.session.add(customer)
    db.session.commit()
    
    # Add a material
    material = Material(
        id=generate_uid('M'),
        name='مادة افتراضية',
        unit='قطعة',
        unit_cost=100
    )
    db.session.add(material)
    db.session.commit()
    
    # Add a partner
    partner = Partner(
        id=generate_uid('PR'),
        name='شريك افتراضي',
        phone='01111111111'
    )
    db.session.add(partner)
    db.session.commit()
    
    # Add a supplier
    supplier = Supplier(
        id=generate_uid('SP'),
        name='مورد افتراضي',
        phone='01222222222'
    )
    db.session.add(supplier)
    db.session.commit()
    
    # Add a contractor
    contractor = Contractor(
        id=generate_uid('CO'),
        name='مقاول افتراضي',
        phone='01333333333',
        specialty='عام'
    )
    db.session.add(contractor)
    db.session.commit()
    
    # Add a broker
    broker = Broker(
        id=generate_uid('BR'),
        name='سمسار افتراضي',
        phone='01444444444'
    )
    db.session.add(broker)
    db.session.commit()
    
    # Add a unit
    unit = Unit(
        id=generate_uid('U'),
        code='U001',
        project_id=project.id,
        unit_type='شقة',
        floor_number=1,
        area=100,
        rooms=2,
        bathrooms=1,
        total_price=1000000,
        status='متاحة'
    )
    db.session.add(unit)
    db.session.commit()
    
    # Add a safe
    safe = Safe(
        id=generate_uid('SF'),
        project_id=project.id,
        name='الخزينة الرئيسية',
        type='cash',
        is_default=True,
        balance=0
    )
    db.session.add(safe)
    db.session.commit()
    
    print("Basic data seeded successfully!")
    print(f"Project: {project.name}")
    print(f"Customer: {customer.name}")
    print(f"Material: {material.name}")
    print(f"Partner: {partner.name}")
    print(f"Supplier: {supplier.name}")
    print(f"Contractor: {contractor.name}")
    print(f"Broker: {broker.name}")
    print(f"Unit: {unit.code}")
    print(f"Safe: {safe.name}")