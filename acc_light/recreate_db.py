#!/usr/bin/env python3
"""Script to recreate the database with new models"""
from app import app, db

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    
    print("Creating all tables...")
    db.create_all()
    
    print("Database recreated successfully!")
    print("Tables created:")
    for table in db.metadata.tables:
        print(f"  - {table}")