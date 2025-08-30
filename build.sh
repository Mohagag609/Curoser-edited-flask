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

# Create tables only if they don't exist (SAFE MODE)
echo "Checking database tables..."
python3 -c "
from app import app, db
with app.app_context():
    print('Creating tables if not exist...')
    db.create_all()
    print('Database tables ready!')
"

echo "=== Build completed successfully ==="