#!/usr/bin/env python3
"""تحليل المشاكل في التطبيق بدون الحاجة لتشغيله"""

import os
import re
import json

def check_missing_blueprints():
    """فحص وجود blueprints مفقودة"""
    print("🔍 فحص Blueprints المفقودة...")
    
    # قراءة ملف __init__.py
    with open('/workspace/acc/__init__.py', 'r') as f:
        init_content = f.read()
    
    # البحث عن blueprints المسجلة
    registered_blueprints = re.findall(r'app\.register_blueprint\(([^)]+)\)', init_content)
    print(f"✅ عدد Blueprints المسجلة: {len(registered_blueprints)}")
    
    # البحث عن استخدامات url_for في القوالب
    print("\n🔍 البحث عن استخدامات url_for في القوالب...")
    template_issues = []
    
    for root, dirs, files in os.walk('/workspace/acc/templates'):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                # البحث عن url_for
                url_for_calls = re.findall(r"url_for\(['\"]([\w.]+)['\"]", content)
                for call in url_for_calls:
                    blueprint = call.split('.')[0]
                    # التحقق من blueprints غير المسجلة
                    if blueprint not in ['main', 'dashboard', 'customers', 'units', 'partners', 
                                        'contracts', 'brokers', 'installments', 'treasury', 
                                        'vouchers', 'reports', 'suppliers', 'contractors', 
                                        'projects', 'materials', 'system', 'settlement', 
                                        'transfers', 'api']:
                        if blueprint != 'static':  # تجاهل static
                            template_issues.append({
                                'file': filepath.replace('/workspace/', ''),
                                'call': call,
                                'blueprint': blueprint
                            })
    
    if template_issues:
        print("\n⚠️ مشاكل محتملة في القوالب:")
        for issue in template_issues:
            print(f"  - {issue['file']}: url_for('{issue['call']}') - Blueprint '{issue['blueprint']}' غير مسجل")
    else:
        print("✅ لا توجد مشاكل في استخدام url_for")

def check_database_issues():
    """فحص مشاكل قاعدة البيانات المحتملة"""
    print("\n🔍 فحص مشاكل قاعدة البيانات...")
    
    # فحص وجود ملف قاعدة البيانات
    db_file = '/workspace/acc_light.db'
    if os.path.exists(db_file):
        size = os.path.getsize(db_file) / 1024 / 1024  # MB
        print(f"✅ ملف قاعدة البيانات موجود ({size:.2f} MB)")
    else:
        print("⚠️ ملف قاعدة البيانات غير موجود!")
    
    # فحص النماذج للحقول المطلوبة
    print("\n🔍 فحص النماذج...")
    models_path = '/workspace/acc/models'
    if os.path.exists(models_path):
        for file in os.listdir(models_path):
            if file.endswith('.py') and file != '__init__.py':
                print(f"  ✅ {file}")

def check_routes_issues():
    """فحص مشاكل المسارات"""
    print("\n🔍 فحص مشاكل المسارات...")
    
    # البحث عن مسارات الحذف في contracts
    contracts_routes = '/workspace/acc/blueprints/contracts/routes.py'
    if os.path.exists(contracts_routes):
        with open(contracts_routes, 'r') as f:
            content = f.read()
            
        # البحث عن مسارات الحذف
        delete_routes = re.findall(r'@bp\.route\([\'"]([^"\']+)[\'"][^)]*\).*?def\s+(\w+)', content, re.DOTALL)
        print("\n📌 مسارات contracts blueprint:")
        for route, func in delete_routes[:10]:  # أول 10 مسارات
            print(f"  - {route} -> {func}()")

def check_javascript_issues():
    """فحص مشاكل JavaScript"""
    print("\n🔍 فحص مشاكل JavaScript...")
    
    # البحث عن ملفات JS
    js_files = []
    for root, dirs, files in os.walk('/workspace'):
        for file in files:
            if file.endswith('.js') and 'node_modules' not in root:
                js_files.append(os.path.join(root, file))
    
    print(f"✅ عدد ملفات JavaScript: {len(js_files)}")
    
    # فحص استخدام deleteContract
    for js_file in js_files:
        with open(js_file, 'r') as f:
            content = f.read()
            if 'deleteContract' in content:
                print(f"  📌 {js_file.replace('/workspace/', '')} يحتوي على deleteContract")

def main():
    print("🔧 تحليل مشاكل التطبيق...\n")
    
    check_missing_blueprints()
    check_database_issues()
    check_routes_issues()
    check_javascript_issues()
    
    print("\n✅ انتهى التحليل!")

if __name__ == '__main__':
    main()