#!/usr/bin/env python3
"""Check for any errors in the application"""

from acc import create_app
import traceback

def check_app():
    try:
        app = create_app()
        print("✓ App created successfully")
        
        with app.app_context():
            # Test critical routes
            with app.test_client() as client:
                routes = [
                    ('/', 'Home'),
                    ('/auth/login', 'Login'),
                    ('/auth/welcome', 'Welcome (requires login)'),
                    ('/select-project', 'Select Project'),
                ]
                
                for route, name in routes:
                    try:
                        print(f"\nTesting {name} ({route})...")
                        response = client.get(route, follow_redirects=False)
                        print(f"  Status: {response.status_code}")
                        
                        if response.status_code == 302:
                            print(f"  Redirects to: {response.headers.get('Location')}")
                        elif response.status_code >= 400:
                            print(f"  ERROR! Response: {response.data.decode()[:200]}")
                    except Exception as e:
                        print(f"  EXCEPTION: {str(e)}")
                        traceback.print_exc()
                        
    except Exception as e:
        print(f"FAILED to create app: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    check_app()