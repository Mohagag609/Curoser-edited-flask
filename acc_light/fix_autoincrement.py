"""Fix autoincrement in all models to be explicit"""
import os
import re

def fix_autoincrement_in_file(filepath):
    """Fix autoincrement in a single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace autoincrement=True with nothing (SQLAlchemy handles it automatically for Integer primary keys)
    content = re.sub(
        r'id = Column\(Integer, primary_key=True, autoincrement=True\)',
        'id = Column(Integer, primary_key=True)',
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed: {filepath}")

def fix_all_models():
    """Fix all model files"""
    models_dir = '/workspace/acc_light/acc/models'
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            fix_autoincrement_in_file(filepath)

if __name__ == '__main__':
    print("Fixing autoincrement in all model files...")
    fix_all_models()
    print("Done!")