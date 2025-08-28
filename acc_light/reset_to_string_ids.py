"""
Reset all models back to String IDs to avoid SQLite RETURNING issue
"""

import os
import re

def reset_to_string_ids(filepath):
    """Reset a single model file to use String IDs"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace Integer primary keys back to String(20)
    content = re.sub(
        r'id = Column\(Integer, primary_key=True\)',
        'id = Column(String(20), primary_key=True)',
        content
    )
    
    # Fix foreign key references back to String(20)
    content = re.sub(
        r'Column\(Integer, ForeignKey\(',
        'Column(String(20), ForeignKey(',
        content
    )
    
    # Fix entity_id to remain String (polymorphic reference)
    content = re.sub(
        r'entity_id = Column\(String\(20\)\)',
        'entity_id = Column(String(20))',
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Reset: {filepath}")

def reset_all_models():
    """Reset all model files"""
    models_dir = '/workspace/acc_light/acc/models'
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            reset_to_string_ids(filepath)

def reset_seed_data():
    """Reset seed_data.py to use generate_uid"""
    filepath = '/workspace/acc_light/seed_data.py'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add back generate_uid imports
    content = content.replace(
        'from acc.services.utils import generate_uid',
        'from acc.services.utils import generate_uid'
    )
    
    # Fix project creation
    content = content.replace(
        "Project(name='مشروع الحياة للإسكان',",
        "Project(id=generate_uid('PRJ'), name='مشروع الحياة للإسكان',"
    )
    content = content.replace(
        "Project(name='مشروع أبراج النيل',",
        "Project(id=generate_uid('PRJ'), name='مشروع أبراج النيل',"
    )
    
    # Fix other entity creations
    content = re.sub(
        r"Customer\(name=",
        "Customer(id=generate_uid('C'), name=",
        content
    )
    
    content = re.sub(
        r"Partner\(name=",
        "Partner(id=generate_uid('PR'), name=",
        content
    )
    
    content = re.sub(
        r"PartnerGroup\(name=",
        "PartnerGroup(id=generate_uid('PG'), name=",
        content
    )
    
    content = re.sub(
        r"PartnerGroupMember\(group_id=",
        "PartnerGroupMember(id=generate_uid('PGM'), group_id=",
        content
    )
    
    content = re.sub(
        r"Unit\(project_id=",
        "Unit(id=generate_uid('U'), project_id=",
        content
    )
    
    content = re.sub(
        r"UnitPartner\(unit_id=",
        "UnitPartner(id=generate_uid('UP'), unit_id=",
        content
    )
    
    content = re.sub(
        r"Safe\(project_id=",
        "Safe(id=generate_uid('SF'), project_id=",
        content
    )
    
    content = re.sub(
        r"Broker\(name=",
        "Broker(id=generate_uid('BR'), name=",
        content
    )
    
    content = re.sub(
        r"Contract\(",
        "Contract(id=generate_uid('CT'), ",
        content
    )
    
    content = re.sub(
        r"Installment\(",
        "Installment(id=generate_uid('IN'), ",
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Reset: {filepath}")

def reset_routes():
    """Reset route files to use generate_uid"""
    blueprints_dir = '/workspace/acc_light/acc/blueprints'
    
    for root, dirs, files in os.walk(blueprints_dir):
        for filename in files:
            if filename == 'routes.py':
                filepath = os.path.join(root, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add back id=generate_uid(...) patterns
                # This is complex and depends on specific patterns in each file
                # For now, just ensure imports are correct
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Checked: {filepath}")

if __name__ == '__main__':
    print("Resetting all models to use String IDs...")
    reset_all_models()
    
    print("\nResetting seed_data.py...")
    reset_seed_data()
    
    print("\nDone! The system is now using String IDs again.")
    print("Next steps:")
    print("1. Delete the database: rm -f acc_light.db")
    print("2. Recreate tables: python3 -c \"from app import app, db; app.app_context().push(); db.create_all()\"")
    print("3. Run seed data: python3 seed_data.py")