#!/usr/bin/env python3
"""إصلاح جميع المشاكل المكتشفة في التطبيق"""

import os
import re

def fix_delete_contract_js():
    """إصلاح مشكلة حذف العقود - إضافة CSRF token"""
    print("🔧 إصلاح مشكلة حذف العقود...")
    
    # قراءة ملف contracts/view.html
    view_file = '/workspace/acc/blueprints/contracts/templates/contracts/view.html'
    with open(view_file, 'r') as f:
        content = f.read()
    
    # تحديث دالة deleteContract لإضافة CSRF token
    old_js = """async function deleteContract(id) {
    if (!confirm('هل أنت متأكد من حذف هذا العقد؟')) {
        return;
    }
    
    try {
        const response = await fetch(`/contracts/${id}/delete`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });"""
    
    new_js = """async function deleteContract(id) {
    if (!confirm('هل أنت متأكد من حذف هذا العقد؟')) {
        return;
    }
    
    try {
        // Get CSRF token if available
        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        const headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        };
        
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken.getAttribute('content');
        }
        
        const response = await fetch(`/contracts/${id}/delete`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({})
        });"""
    
    if old_js in content:
        content = content.replace(old_js, new_js)
        with open(view_file, 'w') as f:
            f.write(content)
        print("  ✅ تم تحديث contracts/view.html")
    
    # تحديث ملف contracts/index.html أيضًا
    index_file = '/workspace/acc/blueprints/contracts/templates/contracts/index.html'
    with open(index_file, 'r') as f:
        content = f.read()
    
    if old_js in content:
        content = content.replace(old_js, new_js)
        with open(index_file, 'w') as f:
            f.write(content)
        print("  ✅ تم تحديث contracts/index.html")

def add_csrf_meta_to_base():
    """إضافة CSRF meta tag إلى base.html"""
    print("\n🔧 إضافة CSRF token إلى base.html...")
    
    base_file = '/workspace/acc/templates/base.html'
    with open(base_file, 'r') as f:
        content = f.read()
    
    # البحث عن </head> وإضافة meta tag قبله
    if '<meta name="csrf-token"' not in content:
        csrf_meta = '    <meta name="csrf-token" content="{{ csrf_token() }}">\n'
        content = content.replace('</head>', csrf_meta + '</head>')
        
        with open(base_file, 'w') as f:
            f.write(content)
        print("  ✅ تم إضافة CSRF meta tag")

def fix_delete_route_methods():
    """تحديث مسار الحذف لقبول DELETE method أيضًا"""
    print("\n🔧 تحديث مسارات الحذف...")
    
    routes_file = '/workspace/acc/blueprints/contracts/routes.py'
    with open(routes_file, 'r') as f:
        content = f.read()
    
    # تحديث route decorator لقبول DELETE method
    old_route = "@bp.route('/<string:id>/delete', methods=['POST'])"
    new_route = "@bp.route('/<string:id>/delete', methods=['POST', 'DELETE'])"
    
    if old_route in content:
        content = content.replace(old_route, new_route)
        with open(routes_file, 'w') as f:
            f.write(content)
        print("  ✅ تم تحديث مسار الحذف لقبول POST و DELETE")

def add_error_logging():
    """إضافة تسجيل أفضل للأخطاء"""
    print("\n🔧 إضافة تسجيل محسّن للأخطاء...")
    
    routes_file = '/workspace/acc/blueprints/contracts/routes.py'
    with open(routes_file, 'r') as f:
        content = f.read()
    
    # إضافة import logging إذا لم يكن موجودًا
    if 'import logging' not in content:
        imports = "from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g"
        new_imports = imports + "\nimport logging"
        content = content.replace(imports, new_imports)
    
    # تحديث exception handler في دالة delete
    old_except = """    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500"""
    
    new_except = """    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting contract {id}: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ في حذف العقد: {str(e)}'}), 500"""
    
    if old_except in content:
        content = content.replace(old_except, new_except)
        
        # إضافة from flask import current_app as app
        if 'from flask import current_app as app' not in content:
            content = content.replace('import logging', 'import logging\nfrom flask import current_app as app')
        
        with open(routes_file, 'w') as f:
            f.write(content)
        print("  ✅ تم إضافة تسجيل محسّن للأخطاء")

def create_requirements_install_script():
    """إنشاء سكريبت لتثبيت المتطلبات"""
    print("\n🔧 إنشاء سكريبت تثبيت المتطلبات...")
    
    script_content = """#!/bin/bash
# سكريبت تثبيت متطلبات التطبيق

echo "🔧 تثبيت متطلبات التطبيق..."

# التحقق من وجود pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 غير مثبت. يرجى تثبيته أولاً."
    exit 1
fi

# محاولة تثبيت المتطلبات
echo "📦 تثبيت المتطلبات..."

# تثبيت Flask ومتطلباته
pip3 install --user Flask==3.0.0 || echo "⚠️ فشل تثبيت Flask"
pip3 install --user Flask-SQLAlchemy==3.1.1 || echo "⚠️ فشل تثبيت Flask-SQLAlchemy"
pip3 install --user python-dotenv==1.0.0 || echo "⚠️ فشل تثبيت python-dotenv"
pip3 install --user Jinja2==3.1.2 || echo "⚠️ فشل تثبيت Jinja2"
pip3 install --user gunicorn==21.2.0 || echo "⚠️ فشل تثبيت gunicorn"
pip3 install --user python-dateutil==2.8.2 || echo "⚠️ فشل تثبيت python-dateutil"

# محاولة تثبيت psycopg2-binary (قد يفشل بدون PostgreSQL)
echo "📦 محاولة تثبيت psycopg2-binary..."
pip3 install --user psycopg2-binary==2.9.9 2>/dev/null || {
    echo "⚠️ فشل تثبيت psycopg2-binary - سيتم استخدام SQLite"
}

echo "✅ انتهى تثبيت المتطلبات!"
echo ""
echo "📌 لتشغيل التطبيق:"
echo "   python3 app.py"
"""
    
    with open('/workspace/install_requirements.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('/workspace/install_requirements.sh', 0o755)
    print("  ✅ تم إنشاء install_requirements.sh")

def create_test_delete_script():
    """إنشاء سكريبت لاختبار حذف العقود"""
    print("\n🔧 إنشاء سكريبت اختبار حذف العقود...")
    
    script_content = """#!/usr/bin/env python3
'''اختبار وظيفة حذف العقود'''

import requests
import json

# URL التطبيق
BASE_URL = 'http://localhost:5000'  # غيّر هذا حسب URL تطبيقك

def test_delete_contract(contract_id):
    '''اختبار حذف عقد'''
    print(f"🧪 اختبار حذف العقد: {contract_id}")
    
    # محاولة حذف العقد
    url = f"{BASE_URL}/contracts/{contract_id}/delete"
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, json={})
        print(f"📡 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ تم حذف العقد بنجاح!")
            else:
                print(f"❌ فشل الحذف: {data.get('message')}")
        else:
            print(f"❌ خطأ HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {str(e)}")

if __name__ == '__main__':
    # اختبار مع معرف عقد (غيّر هذا لمعرف عقد حقيقي)
    test_contract_id = 'CONTRACT-001'  # ضع معرف عقد حقيقي هنا
    test_delete_contract(test_contract_id)
"""
    
    with open('/workspace/test_delete_contract.py', 'w') as f:
        f.write(script_content)
    
    os.chmod('/workspace/test_delete_contract.py', 0o755)
    print("  ✅ تم إنشاء test_delete_contract.py")

def main():
    print("🚀 بدء إصلاح جميع المشاكل...\n")
    
    fix_delete_contract_js()
    add_csrf_meta_to_base()
    fix_delete_route_methods()
    add_error_logging()
    create_requirements_install_script()
    create_test_delete_script()
    
    print("\n✅ تم إصلاح جميع المشاكل!")
    print("\n📋 الخطوات التالية:")
    print("1. شغّل ./install_requirements.sh لتثبيت المتطلبات")
    print("2. شغّل python3 app.py لتشغيل التطبيق")
    print("3. استخدم test_delete_contract.py لاختبار حذف العقود")

if __name__ == '__main__':
    main()