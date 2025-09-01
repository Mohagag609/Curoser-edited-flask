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

# Run fixes for known issues
echo "Running application fixes..."
if [ -f "fix_all_issues.py" ]; then
    echo "Applying all known fixes..."
    python3 fix_all_issues.py || echo "Warning: Some fixes may have failed"
fi

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

# Run database fixes if needed
echo "Checking for database fixes..."
if [ -f "fix_db_errors.py" ]; then
    echo "Running database fixes..."
    python3 fix_db_errors.py || echo "Warning: Database fixes may have partially failed"
fi

# Run quick fixes if available
if [ -f "quick_fix.py" ]; then
    echo "Running quick fixes..."
    python3 quick_fix.py || echo "Warning: Quick fixes may have partially failed"
fi

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

# Summary of fixes added:
# 1. fix_all_issues.py - Fixes CSRF tokens, delete routes, and error logging
# 2. fix_db_errors.py - Adds missing database columns
# 3. quick_fix.py - Quick database connection fixes