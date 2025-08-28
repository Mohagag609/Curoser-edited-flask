"""
Fix all models to use Integer IDs with autoincrement
"""

import os
import re

def fix_model_file(filepath):
    """Fix a single model file to use Integer IDs"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace String(20) primary keys with Integer autoincrement
    content = re.sub(
        r'id = Column\(String\(20\), primary_key=True\)',
        'id = Column(Integer, primary_key=True, autoincrement=True)',
        content
    )
    
    # Fix foreign key references from String(20) to Integer
    content = re.sub(
        r'Column\(String\(20\), ForeignKey\(',
        'Column(Integer, ForeignKey(',
        content
    )
    
    # Fix entity_id to remain String (polymorphic reference)
    content = re.sub(
        r'entity_id = Column\(Integer\)',
        'entity_id = Column(String(20))',
        content
    )
    
    # Add Integer import if not present
    if 'from sqlalchemy import' in content and 'Integer' not in content:
        content = re.sub(
            r'(from sqlalchemy import .*?)(Column|String)',
            r'\1Integer, \2',
            content,
            count=1
        )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed: {filepath}")

def fix_all_models():
    """Fix all model files in the models directory"""
    models_dir = '/workspace/acc_light/acc/models'
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            fix_model_file(filepath)

def fix_seed_data():
    """Fix seed_data.py to remove generate_uid calls"""
    filepath = '/workspace/acc_light/seed_data.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove id=generate_uid(...) patterns
    content = re.sub(r'id=generate_uid\([\'"][A-Z-]+[\'"]\),\s*', '', content)
    
    # Fix imports
    content = content.replace(
        'from acc.models import Customer, Unit, Partner, Safe, PartnerGroup, PartnerGroupMember, UnitPartner, Broker, Contract, Installment, Project',
        'from acc.models import Customer, Unit, Partner, Safe, PartnerGroup, PartnerGroupMember, UnitPartner, Broker, Contract, Installment, Project'
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed: {filepath}")

def fix_routes():
    """Fix route files to remove generate_uid calls"""
    blueprints_dir = '/workspace/acc_light/acc/blueprints'
    
    for root, dirs, files in os.walk(blueprints_dir):
        for filename in files:
            if filename == 'routes.py':
                filepath = os.path.join(root, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove id=generate_uid(...) patterns
                content = re.sub(r'id=generate_uid\([\'"][A-Z-]+[\'"]\),\s*', '', content)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Fixed: {filepath}")

if __name__ == '__main__':
    print("Fixing all models to use Integer IDs...")
    fix_all_models()
    
    print("\nFixing seed_data.py...")
    fix_seed_data()
    
    print("\nFixing route files...")
    fix_routes()
    
    print("\nDone! Next steps:")
    print("1. Delete the database: rm -f acc_light.db")
    print("2. Recreate tables: python3 -c \"from app import app, db; app.app_context().push(); db.create_all()\"")
    print("3. Run seed data: python3 seed_data.py")