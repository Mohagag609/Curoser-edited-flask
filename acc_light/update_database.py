"""
Update existing database schema to match current models
This script adds missing columns without dropping tables
"""

from app import app, db
from sqlalchemy import text

def update_database():
    with app.app_context():
        print("Checking database schema...")
        
        # Get database connection
        with db.engine.connect() as conn:
            try:
                # Try to add missing columns to projects table
                print("Updating projects table...")
                conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE"))
                conn.commit()
                print("Added is_default column to projects table")
            except Exception as e:
                print(f"Error updating projects table: {e}")
                conn.rollback()
            
            try:
                # Add project_id to units table if missing
                print("Updating units table...")
                conn.execute(text("ALTER TABLE units ADD COLUMN IF NOT EXISTS project_id VARCHAR(20)"))
                conn.commit()
                print("Added project_id column to units table")
            except Exception as e:
                print(f"Error updating units table: {e}")
                conn.rollback()
            
            try:
                # Add project_id to contracts table if missing
                print("Updating contracts table...")
                conn.execute(text("ALTER TABLE contracts ADD COLUMN IF NOT EXISTS project_id VARCHAR(20)"))
                conn.commit()
                print("Added project_id column to contracts table")
            except Exception as e:
                print(f"Error updating contracts table: {e}")
                conn.rollback()
            
            try:
                # Add project_id to safes table if missing
                print("Updating safes table...")
                conn.execute(text("ALTER TABLE safes ADD COLUMN IF NOT EXISTS project_id VARCHAR(20)"))
                conn.commit()
                print("Added project_id column to safes table")
            except Exception as e:
                print(f"Error updating safes table: {e}")
                conn.rollback()
            
            try:
                # Add project_id to vouchers table if missing
                print("Updating vouchers table...")
                conn.execute(text("ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS project_id VARCHAR(20)"))
                conn.execute(text("ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS entity_type VARCHAR(20)"))
                conn.execute(text("ALTER TABLE vouchers ADD COLUMN IF NOT EXISTS entity_id VARCHAR(20)"))
                conn.commit()
                print("Added missing columns to vouchers table")
            except Exception as e:
                print(f"Error updating vouchers table: {e}")
                conn.rollback()
        
        # Now create any missing tables
        print("Creating any missing tables...")
        db.create_all()
        
        print("Database update completed!")

if __name__ == '__main__':
    update_database()