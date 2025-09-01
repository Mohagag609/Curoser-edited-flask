#!/usr/bin/env python3
"""
Test script for Real Estate System
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported"""
    try:
        from app import app, db, Property, Agent, Client, Inquiry
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database operations"""
    try:
        from app import app, db, Property, Agent
        
        with app.app_context():
            # Test database connection
            properties_count = Property.query.count()
            agents_count = Agent.query.count()
            
            print(f"✅ Database connection successful")
            print(f"   Properties in database: {properties_count}")
            print(f"   Agents in database: {agents_count}")
            return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_routes():
    """Test if routes are properly configured"""
    try:
        from app import app
        
        with app.test_client() as client:
            # Test main route
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Main route working")
            else:
                print(f"❌ Main route failed: {response.status_code}")
                return False
            
            # Test properties route
            response = client.get('/properties')
            if response.status_code == 200:
                print("✅ Properties route working")
            else:
                print(f"❌ Properties route failed: {response.status_code}")
                return False
            
            # Test admin route
            response = client.get('/admin')
            if response.status_code == 200:
                print("✅ Admin route working")
            else:
                print(f"❌ Admin route failed: {response.status_code}")
                return False
            
            return True
    except Exception as e:
        print(f"❌ Route test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Real Estate System...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Database Test", test_database),
        ("Routes Test", test_routes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\n🚀 To start the application:")
        print("   python3 app.py")
        print("\n🌐 Then visit: http://localhost:5000")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)