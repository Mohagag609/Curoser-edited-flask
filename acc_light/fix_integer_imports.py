import os
import re

def fix_imports_in_file(filepath):
    """Fix imports in a single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file uses Integer but doesn't import it
    if 'Column(Integer' in content and 'import' in content:
        # Find the sqlalchemy import line
        import_match = re.search(r'from sqlalchemy import (.*)', content)
        if import_match:
            imports = import_match.group(1)
            if 'Integer' not in imports:
                # Add Integer to imports
                new_imports = 'Integer, ' + imports
                content = content.replace(
                    f'from sqlalchemy import {imports}',
                    f'from sqlalchemy import {new_imports}'
                )
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Fixed imports in: {filepath}")

def fix_all_models():
    """Fix all model files"""
    models_dir = '/workspace/acc_light/acc/models'
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            fix_imports_in_file(filepath)

if __name__ == '__main__':
    print("Fixing Integer imports in all model files...")
    fix_all_models()
    print("Done!")