"""Fix route files to use generate_uid for String IDs"""
import os
import re

def fix_route_file(filepath):
    """Fix a single route file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Common entity patterns to fix
    patterns = [
        # Units
        (r'unit = Unit\(\s*project_id=', 'unit = Unit(\n            id=generate_uid(\'U\'),\n            project_id='),
        # Customers
        (r'customer = Customer\(\s*name=', 'customer = Customer(\n            id=generate_uid(\'C\'),\n            name='),
        # Partners
        (r'partner = Partner\(\s*name=', 'partner = Partner(\n            id=generate_uid(\'PR\'),\n            name='),
        # Contracts
        (r'contract = Contract\(\s*project_id=', 'contract = Contract(\n            id=generate_uid(\'CT\'),\n            project_id='),
        # Safes
        (r'safe = Safe\(\s*project_id=', 'safe = Safe(\n            id=generate_uid(\'SF\'),\n            project_id='),
        # Vouchers
        (r'voucher = Voucher\(\s*project_id=', 'voucher = Voucher(\n            id=generate_uid(\'V\'),\n            project_id='),
        # Brokers
        (r'broker = Broker\(\s*name=', 'broker = Broker(\n            id=generate_uid(\'BR\'),\n            name='),
        # Suppliers
        (r'supplier = Supplier\(\s*name=', 'supplier = Supplier(\n            id=generate_uid(\'SP\'),\n            name='),
        # Contractors
        (r'contractor = Contractor\(\s*name=', 'contractor = Contractor(\n            id=generate_uid(\'CO\'),\n            name='),
        # Projects
        (r'project = Project\(\s*name=', 'project = Project(\n            id=generate_uid(\'PRJ\'),\n            name='),
        # Materials
        (r'material = Material\(\s*name=', 'material = Material(\n            id=generate_uid(\'MT\'),\n            name='),
        # ProjectStages
        (r'stage = ProjectStage\(\s*project_id=', 'stage = ProjectStage(\n            id=generate_uid(\'PS\'),\n            project_id='),
        # ProjectMaterials
        (r'pm = ProjectMaterial\(\s*project_id=', 'pm = ProjectMaterial(\n            id=generate_uid(\'PM\'),\n            project_id='),
    ]
    
    # Apply all patterns
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed: {filepath}")

def fix_all_routes():
    """Fix all route files"""
    blueprints_dir = '/workspace/acc_light/acc/blueprints'
    
    for root, dirs, files in os.walk(blueprints_dir):
        for filename in files:
            if filename == 'routes.py':
                filepath = os.path.join(root, filename)
                fix_route_file(filepath)

if __name__ == '__main__':
    print("Fixing all route files to use generate_uid...")
    fix_all_routes()
    print("Done!")