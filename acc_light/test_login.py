#!/usr/bin/env python3
"""Test login flow"""

from acc import create_app

def test_login():
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            # Test login page
            print("1. Testing login page...")
            response = client.get('/auth/login')
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Error: {response.data.decode()[:200]}")
            
            # Test login
            print("\n2. Testing login...")
            response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=False)
            print(f"   Status: {response.status_code}")
            print(f"   Location: {response.headers.get('Location', 'No redirect')}")
            
            # Follow redirect
            if response.status_code == 302:
                print("\n3. Following redirect...")
                response = client.get(response.headers['Location'])
                print(f"   Status: {response.status_code}")
                if response.status_code != 200:
                    print(f"   Error: {response.data.decode()[:200]}")

if __name__ == "__main__":
    test_login()