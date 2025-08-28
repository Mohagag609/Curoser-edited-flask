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

# DROP AND RECREATE ALL TABLES
echo "Recreating database tables..."
python3 -c "
from app import app, db
with app.app_context():
    print('Dropping all existing tables...')
    db.drop_all()
    print('Creating fresh tables...')
    db.create_all()
    print('Database tables created successfully')
"

# Seed initial data
echo "Seeding initial data..."
python3 seed_data.py

echo "=== Build completed successfully ==="