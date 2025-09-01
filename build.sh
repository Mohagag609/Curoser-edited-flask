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

# Check if this is the first deployment or optimization needed
OPTIMIZATION_FLAG="/opt/render/project/.optimizations_done"

if [ ! -f "$OPTIMIZATION_FLAG" ]; then
    echo "First deployment detected - Running optimizations..."
    
    # Run database optimizations (once only)
    if [ -f "database_optimizations.py" ]; then
        python3 database_optimizations.py && touch "$OPTIMIZATION_FLAG" || echo "Optimizations failed, continuing..."
    fi
    
    # Run performance boost (once only)
    if [ -f "performance_boost.py" ]; then
        python3 performance_boost.py indexes || echo "Performance boost failed, continuing..."
    fi
else
    echo "Optimizations already applied - skipping..."
fi

echo "=== Build completed successfully ==="