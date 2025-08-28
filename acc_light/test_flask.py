#!/usr/bin/env python3
import os
os.environ['FLASK_DEBUG'] = '1'
os.environ['FLASK_ENV'] = 'development'

from app import app

if __name__ == '__main__':
    print("Starting Flask in DEBUG mode...")
    app.run(host='0.0.0.0', port=5000, debug=True)