#!/usr/bin/env python3
"""Test script to check app functionality"""

from acc import create_app
from acc.extensions import db

def test_app():
    """Test basic app functionality"""
    print("Creating app...")
    app = create_app()
    
    with app.app_context():
        print("\nTesting database connection...")
        try:
            # Test database
            from acc.models import Project, Customer, Contract
            
            project_count = Project.query.count()
            print(f"✓ Projects: {project_count}")
            
            customer_count = Customer.query.count()
            print(f"✓ Customers: {customer_count}")
            
            contract_count = Contract.query.count()
            print(f"✓ Contracts: {contract_count}")
            
            print("\n✅ App is working correctly!")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_app()