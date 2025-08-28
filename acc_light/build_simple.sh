#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies and build CSS
npm install
npm run build

# Create database tables directly
python3 create_db.py

# Create initial data if needed (ignore errors)
python3 seed_data.py || echo "Seed data skipped"