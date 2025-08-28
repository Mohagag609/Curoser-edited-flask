#!/usr/bin/env python3
"""Clean migration state from database."""

from app import app
from acc.extensions import db
from sqlalchemy import text

def clean_migrations():
    """Remove alembic version tracking from database."""
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Check if alembic_version table exists
                result = conn.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables "
                    "WHERE table_name = 'alembic_version')"
                ))
                exists = result.scalar()
                
                if exists:
                    # Get current version
                    result = conn.execute(text("SELECT version_num FROM alembic_version"))
                    version = result.scalar()
                    print(f"Current migration version: {version}")
                    
                    # Drop the table
                    conn.execute(text("DROP TABLE alembic_version"))
                    conn.commit()
                    print("Cleaned migration state successfully")
                else:
                    print("No migration state found")
                    
        except Exception as e:
            print(f"Error cleaning migrations: {e}")

if __name__ == '__main__':
    clean_migrations()