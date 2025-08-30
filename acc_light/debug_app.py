#!/usr/bin/env python3
"""Debug script to find errors"""

from acc import create_app
import traceback

def test_routes():
    """Test all main routes"""
    app = create_app()
    
    routes_to_test = [
        ('/', 'Home'),
        ('/auth/login', 'Login'),
        ('/auth/welcome', 'Welcome'),
        ('/projects/', 'Projects'),
        ('/customers/', 'Customers'),
        ('/select-project', 'Select Project'),
    ]
    
    with app.app_context():
        with app.test_client() as client:
            for route, name in routes_to_test:
                try:
                    print(f"\nTesting {name} ({route})...")
                    response = client.get(route, follow_redirects=False)
                    print(f"Status: {response.status_code}")
                    
                    if response.status_code >= 500:
                        print(f"ERROR: Server error on {route}")
                        print("Response data:", response.data[:200])
                        
                except Exception as e:
                    print(f"EXCEPTION on {route}: {str(e)}")
                    traceback.print_exc()

if __name__ == "__main__":
    test_routes()