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

# Clean any existing alembic version
echo "Cleaning database state..."
python3 clean_migrations.py || true

# Create database tables directly
echo "Creating database tables..."
python3 create_db.py

# Fix model relationships
echo "Fixing model relationships..."
python3 fix_models.py || true

# Create initial data if needed
echo "Seeding initial data..."
python3 seed_data.py || echo "Seed data skipped"

echo "=== Build completed successfully ==="