#!/usr/bin/env python3
"""Run app in debug mode"""

from acc import create_app

if __name__ == '__main__':
    app = create_app()
    app.config['DEBUG'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    print("Starting app in debug mode...")
    print("Open http://localhost:5000 in your browser")
    print("Login with: admin / admin123")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)