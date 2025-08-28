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

# Initialize database migrations if needed
if [ ! -d "migrations" ]; then
    echo "Initializing migrations..."
    flask db init
fi

# Create initial migration if no versions exist
if [ ! "$(ls -A migrations/versions 2>/dev/null)" ]; then
    echo "Creating initial migration..."
    flask db migrate -m "Initial migration"
fi

# Run database migrations (with fallback)
flask db upgrade || {
    echo "Migration failed, creating tables directly..."
    python3 create_db.py
}

# Create initial data if needed (ignore errors)
python3 seed_data.py || echo "Seed data skipped"