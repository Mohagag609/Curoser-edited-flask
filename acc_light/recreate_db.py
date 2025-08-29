#!/usr/bin/env python3
"""Script to recreate the database with new models"""
from app import app, db
from sqlalchemy import text

with app.app_context():
    print("Dropping all tables with CASCADE...")
    
    # Get all table names
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    
    # Drop all tables with CASCADE
    with db.engine.connect() as conn:
        # For PostgreSQL, use CASCADE
        if db.engine.dialect.name == 'postgresql':
            for table in tables:
                try:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
                    print(f'Dropped table: {table}')
                except Exception as e:
                    print(f'Warning dropping {table}: {e}')
            conn.commit()
        else:
            # For SQLite, just use drop_all
            db.drop_all()
    
    print("Creating all tables...")
    db.create_all()
    
    print("Database recreated successfully!")
    print("Tables created:")
    for table in db.metadata.tables:
        print(f"  - {table}")