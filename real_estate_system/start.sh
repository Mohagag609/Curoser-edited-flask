#!/bin/bash

echo "🏠 Starting Real Estate System..."
echo "================================="

# Check if database exists
if [ ! -f "real_estate.db" ]; then
    echo "📦 Creating database..."
    python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database created successfully!')
"
fi

echo "🚀 Starting Flask application..."
echo "🌐 Application will be available at: http://localhost:5000"
echo "📊 Admin panel: http://localhost:5000/admin"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Start the application
python3 app.py