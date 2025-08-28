#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies and build CSS
npm install
npm run build

# Run database migrations
flask db upgrade

# Create initial data if needed
python3 seed_data.py || true