#!/usr/bin/env bash
# exit on error
set -o errexit

echo "=== Starting optimized build process ==="

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

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p backups
mkdir -p uploads
mkdir -p reports

# Set permissions
chmod 755 logs backups uploads reports

# Reset database to fix relationship conflicts
echo "Resetting database to fix relationship conflicts..."
python3 reset_db_simple.py

# Initialize optimized application
echo "Initializing optimized application..."
python3 -c "
from acc import create_app
from acc.core.database_simple import get_database_stats_simple
from acc.core.backup import create_automatic_backup

app = create_app()
with app.app_context():
    print('✅ Optimized application initialized')
    
    # Display database stats
    try:
        stats = get_database_stats_simple(app)
        print('📊 Database Statistics:')
        for table, count in stats.items():
            print(f'   {table}: {count:,} records')
    except Exception as e:
        print(f'⚠️ Could not get database stats: {e}')
    
    # Create initial backup
    try:
        if create_automatic_backup():
            print('✅ Initial backup created')
        else:
            print('⚠️ Backup creation failed')
    except Exception as e:
        print(f'⚠️ Backup error: {e}')
"

echo "=== Optimized build completed successfully ==="
echo "🌐 Run with: python run_optimized.py"