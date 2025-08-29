#!/bin/bash

echo "Starting ACC Light Application..."
echo "================================="

# Kill any existing processes
killall -9 python3 2>/dev/null || true
killall -9 flask 2>/dev/null || true

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Navigate to project directory
cd /workspace/acc_light

# Run Flask
echo "Starting Flask server on http://localhost:5000"
python3 -m flask run --host=0.0.0.0 --port=5000