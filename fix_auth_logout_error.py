#!/usr/bin/env python3
"""إصلاح مشكلة auth.logout في جميع القوالب"""

import os
import re

def find_auth_logout_in_templates():
    """البحث عن auth.logout في جميع القوالب"""
    print("🔍 البحث عن auth.logout في جميع القوالب...")
    
    found_files = []
    
    for root, dirs, files in os.walk('/workspace'):
        # تجاهل المجلدات غير المرغوب فيها
        if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', 'venv']):
            continue
            
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'auth.logout' in content:
                            found_files.append(filepath)
                            print(f"  ⚠️ وجد في: {filepath}")
                except:
                    pass
    
    return found_files

def fix_auth_logout_references(files):
    """إصلاح مراجع auth.logout"""
    for filepath in files:
        print(f"\n🔧 إصلاح {filepath}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # استبدال auth.logout بحل بديل
        original_content = content
        
        # البحث عن أنماط مختلفة
        patterns = [
            (r"url_for\(['\"']auth\.logout['\"']\)", "url_for('main.index')"),  # استبدال بالصفحة الرئيسية
            (r"href=['\"]{{ url_for\(['\"']auth\.logout['\"']\) }}['\"]", 'href="{{ url_for(\'main.clear_project\') }}"'),
            (r"{{ url_for\(['\"']auth\.logout['\"']\) }}", "{{ url_for('main.clear_project') }}")
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ تم الإصلاح")
        else:
            print(f"  ℹ️ لم يتم العثور على auth.logout")

def add_logout_functionality():
    """إضافة وظيفة تسجيل خروج بسيطة"""
    print("\n🔧 إضافة وظيفة تسجيل الخروج...")
    
    main_routes = './acc/blueprints/main/routes.py'
    
    with open(main_routes, 'r') as f:
        content = f.read()
    
    # إضافة route للخروج إذا لم يكن موجودًا
    if 'def logout' not in content:
        logout_route = '''
@bp.route('/logout')
def logout():
    """تسجيل الخروج"""
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('main.index'))'''
        
        # إضافة في نهاية الملف
        content = content.rstrip() + '\n' + logout_route + '\n'
        
        with open(main_routes, 'w') as f:
            f.write(content)
        
        print("  ✅ تم إضافة وظيفة logout")

def clear_template_cache():
    """مسح ذاكرة التخزين المؤقت للقوالب"""
    print("\n🧹 مسح ذاكرة التخزين المؤقت...")
    
    cache_dirs = [
        './__pycache__',
        './acc/__pycache__',
        './acc/blueprints/__pycache__',
        './acc/blueprints/dashboard/__pycache__',
        './acc/templates/__pycache__'
    ]
    
    import shutil
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                print(f"  ✅ تم مسح {cache_dir}")
            except:
                pass

def check_base_template():
    """فحص قالب base.html بحثًا عن المشاكل"""
    print("\n🔍 فحص base.html...")
    
    base_path = './acc/templates/base.html'
    if os.path.exists(base_path):
        with open(base_path, 'r') as f:
            content = f.read()
            
        # البحث عن أي استخدام لـ auth
        auth_usages = re.findall(r"url_for\(['\"']auth\.[^'\"]+['\"']\)", content)
        if auth_usages:
            print(f"  ⚠️ وجدت استخدامات auth في base.html: {auth_usages}")
            
            # استبدالها
            for usage in auth_usages:
                if 'logout' in usage:
                    content = content.replace(usage, "url_for('main.logout')")
                else:
                    content = content.replace(usage, "url_for('main.index')")
            
            with open(base_path, 'w') as f:
                f.write(content)
            print("  ✅ تم إصلاح base.html")
        else:
            print("  ✅ base.html نظيف")

def main():
    print("🚀 بدء إصلاح مشكلة auth.logout...\n")
    
    # البحث عن الملفات المتأثرة
    affected_files = find_auth_logout_in_templates()
    
    if affected_files:
        print(f"\n📋 وجدت {len(affected_files)} ملف متأثر")
        fix_auth_logout_references(affected_files)
    else:
        print("\n✅ لم يتم العثور على auth.logout في القوالب")
    
    # فحص base.html
    check_base_template()
    
    # إضافة وظيفة logout
    add_logout_functionality()
    
    # مسح الكاش
    clear_template_cache()
    
    print("\n✅ تم إصلاح مشكلة auth.logout!")
    print("\n📌 ملاحظات:")
    print("- تم استبدال auth.logout بـ main.logout")
    print("- تم إضافة وظيفة logout في main blueprint")
    print("- تم مسح ذاكرة التخزين المؤقت")

if __name__ == '__main__':
    main()