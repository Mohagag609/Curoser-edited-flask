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

# NO MIGRATIONS - just create tables directly
echo "Creating database tables..."
python3 -c "
from app import app, db
with app.app_context():
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