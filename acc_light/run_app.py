#!/usr/bin/env python3
import os
import sys

# Kill any existing Flask processes
os.system("killall -9 python3 2>/dev/null || true")

print("Starting ACC Light application...")
print("=" * 50)

try:
    from app import app
    from acc.extensions import db
    
    # Test database connection
    with app.app_context():
        try:
            from acc.models import Project
            projects = Project.query.count()
            print(f"✓ Database connected - Found {projects} projects")
        except Exception as e:
            print(f"✗ Database error: {e}")
    
    print("✓ Application loaded successfully")
    print("=" * 50)
    print("Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=False)
    
except Exception as e:
    print(f"\n✗ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)