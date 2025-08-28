#!/usr/bin/env python3
"""Reset database completely - USE WITH CAUTION!"""

import os
from app import app
from acc.extensions import db
from sqlalchemy import text

def reset_database():
    """Drop all tables and recreate them."""
    with app.app_context():
        print("WARNING: This will delete ALL data!")
        
        # Only proceed in development or with explicit confirmation
        if os.environ.get('FLASK_ENV') == 'production':
            confirm = os.environ.get('CONFIRM_RESET', '').lower()
            if confirm != 'yes':
                print("Skipping reset in production. Set CONFIRM_RESET=yes to proceed.")
                return
        
        try:
            # Drop alembic version table
            with db.engine.connect() as conn:
                conn.execute(text('DROP TABLE IF EXISTS alembic_version'))
                conn.commit()
            print("Dropped alembic_version table")
        except Exception as e:
            print(f"Could not drop alembic_version: {e}")
        
        # Drop all tables
        print("Dropping all tables...")
        db.drop_all()
        
        # Recreate all tables
        print("Creating all tables...")
        db.create_all()
        
        print("Database reset complete!")

if __name__ == '__main__':
    reset_database()