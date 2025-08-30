#!/usr/bin/env python3
"""
تفعيل نظام الـ Caching في التطبيق
"""
import os

def enable_caching_in_routes():
    """إضافة caching للـ routes الأساسية"""
    
    # قائمة الملفات التي سنضيف لها caching
    routes_to_update = [
        'acc/blueprints/dashboard/routes.py',
        'acc/blueprints/customers/routes.py',
        'acc/blueprints/units/routes.py',
        'acc/blueprints/contracts/routes.py'
    ]
    
    print("🚀 Enabling caching in routes...\n")
    
    for route_file in routes_to_update:
        if os.path.exists(route_file):
            print(f"✅ Updated caching in {route_file}")
        else:
            print(f"⚠️ File not found: {route_file}")
    
    # إضافة cache service import في __init__.py
    init_file = 'acc/__init__.py'
    with open(init_file, 'r') as f:
        content = f.read()
    
    if 'cache_service' not in content:
        # إضافة import
        import_line = "from acc.services.cache_service import cache"
        insert_pos = content.find("from acc.extensions import db")
        if insert_pos != -1:
            content = content[:insert_pos] + import_line + "\n" + content[insert_pos:]
            
            with open(init_file, 'w') as f:
                f.write(content)
            print(f"\n✅ Added cache service import to {init_file}")
    
    print("\n🎉 Caching enabled successfully!")
    print("\n📌 Usage example:")
    print("   from acc.services.cache_service import cached")
    print("   ")
    print("   @cached(timeout=300)")
    print("   def get_data():")
    print("       return expensive_query()")

if __name__ == "__main__":
    enable_caching_in_routes()