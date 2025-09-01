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

# Initialize optimized application
echo "Initializing optimized application..."
python3 -c "
from acc import create_app
from acc.core.database import get_database_stats
from acc.core.backup import create_automatic_backup

app = create_app()
with app.app_context():
    print('✅ Optimized application initialized')
    
    # Display database stats
    try:
        stats = get_database_stats(app)
        print('📊 Database Statistics:')
        for table, count in stats.items():
            if not table.startswith('database_'):
                print(f'   {table}: {count:,} records')
        
        if 'database_size_mb' in stats:
            print(f'   Database size: {stats[\"database_size_mb\"]} MB')
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