#!/usr/bin/env bash
# exit on error
set -o errexit

echo "=== Starting build process ==="

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node dependencies and build CSS
echo "Installing Node dependencies and building CSS..."
npm install
npm run build

# NO MIGRATIONS - recreate tables if needed
echo "Managing database tables..."
python3 -c "
from app import app, db
from sqlalchemy import inspect, text

with app.app_context():
    # Check if we need to drop and recreate tables
    inspector = inspect(db.engine)
    
    # Check if projects table exists and has is_default column
    need_recreate = False
    
    if 'projects' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('projects')]
        if 'is_default' not in columns:
            print('Projects table is missing is_default column - will recreate all tables')
            need_recreate = True
    
    if need_recreate:
        print('Dropping all existing tables...')
        db.drop_all()
        print('Creating fresh tables...')
        db.create_all()
        print('Database tables recreated successfully')
    else:
        print('Creating any missing tables...')
        db.create_all()
        print('Database tables created successfully')
"

# Seed initial data if needed
echo "Checking for initial data..."
python3 -c "
from app import app, db
from acc.models import Project

with app.app_context():
    if Project.query.count() == 0:
        print('No projects found, running seed...')
        import seed_data
        seed_data.seed_database()
    else:
        print('Database already has data, skipping seed')
"

echo "=== Build completed successfully ==="