#!/usr/bin/env python3
"""Test project add functionality"""

from acc import create_app
import json

def test_project_add():
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            # Login first
            print("1. Logging in...")
            response = client.post('/auth/login', data={
                'username': 'admin',
                'password': 'admin123'
            })
            print(f"Login status: {response.status_code}")
            
            # Try to add a project
            print("\n2. Adding a new project...")
            response = client.post('/projects/add', 
                data={
                    'name': 'مشروع تجريبي جديد',
                    'project_type': 'عقاري',
                    'location': 'الرياض',
                    'area': '5000',
                    'budget': '10000000',
                    'start_date': '2025-01-01',
                    'end_date': '2026-12-31',
                    'status': 'نشط',
                    'description': 'مشروع تجريبي'
                },
                headers={
                    'X-Requested-With': 'XMLHttpRequest'
                }
            )
            
            print(f"Add project status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = json.loads(response.data)
                    print(f"Response: {json.dumps(data, ensure_ascii=False, indent=2)}")
                except:
                    print(f"Response text: {response.data.decode()[:500]}")
            else:
                print(f"Error response: {response.data.decode()[:500]}")
            
            # Check redirect URL
            print("\n3. Testing redirect...")
            if response.status_code == 200:
                data = json.loads(response.data)
                if 'redirect' in data:
                    print(f"Redirect URL: {data['redirect']}")
                    
                    # Try to access the redirect URL
                    redirect_response = client.get(data['redirect'])
                    print(f"Redirect page status: {redirect_response.status_code}")

if __name__ == "__main__":
    test_project_add()