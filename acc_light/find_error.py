#!/usr/bin/env python3
"""Find which page is causing the error"""

from acc import create_app
from flask import session

def test_specific_routes():
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            # Login first
            print("Logging in...")
            response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)
            
            print(f"Login response: {response.status_code}")
            
            # Test specific routes after login
            routes = [
                '/auth/welcome',
                '/projects/',
                '/projects/add',
                '/customers/',
                '/customers/add',
                '/select-project',
                '/dashboard/'
            ]
            
            for route in routes:
                print(f"\nTesting {route}...")
                try:
                    response = client.get(route)
                    print(f"Status: {response.status_code}")
                    
                    if response.status_code == 500:
                        print("ERROR FOUND!")
                        print("Response:", response.data.decode()[:500])
                        
                except Exception as e:
                    print(f"EXCEPTION: {str(e)}")

if __name__ == "__main__":
    test_specific_routes()