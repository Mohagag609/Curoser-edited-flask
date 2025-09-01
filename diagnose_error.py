#!/usr/bin/env python3
"""تشخيص مشكلة Internal Server Error"""

import os
import sys

# تعيين متغيرات البيئة
os.environ['FLASK_APP'] = 'app'
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = 'True'

print("🔍 تشخيص مشكلة Internal Server Error...\n")

try:
    print("1️⃣ اختبار استيراد التطبيق...")
    from acc import create_app
    print("   ✅ نجح استيراد create_app")
    
    print("\n2️⃣ محاولة إنشاء التطبيق...")
    app = create_app()
    print("   ✅ نجح إنشاء التطبيق")
    
    print("\n3️⃣ اختبار قاعدة البيانات...")
    with app.app_context():
        from acc.extensions import db
        from acc.models import Project
        
        try:
            # اختبار الاتصال
            db.session.execute("SELECT 1")
            print("   ✅ الاتصال بقاعدة البيانات يعمل")
            
            # اختبار query بسيط
            project_count = Project.query.count()
            print(f"   ✅ عدد المشاريع: {project_count}")
            
        except Exception as e:
            print(f"   ❌ خطأ في قاعدة البيانات: {str(e)}")
    
    print("\n4️⃣ اختبار المسارات الرئيسية...")
    with app.test_client() as client:
        # اختبار الصفحة الرئيسية
        try:
            response = client.get('/')
            print(f"   - الصفحة الرئيسية (/): {response.status_code}")
            if response.status_code >= 500:
                print(f"     ❌ خطأ: {response.data[:200]}")
        except Exception as e:
            print(f"   ❌ خطأ في اختبار الصفحة الرئيسية: {str(e)}")
        
        # اختبار صفحة اختيار المشروع
        try:
            response = client.get('/select-project')
            print(f"   - صفحة اختيار المشروع: {response.status_code}")
            if response.status_code >= 500:
                print(f"     ❌ خطأ: {response.data[:200]}")
        except Exception as e:
            print(f"   ❌ خطأ في اختبار صفحة المشروع: {str(e)}")
    
    print("\n5️⃣ فحص القوالب...")
    template_dirs = [
        '/workspace/acc/templates',
        '/workspace/acc/blueprints/dashboard/templates',
        '/workspace/acc/blueprints/main/templates'
    ]
    
    for dir_path in template_dirs:
        if os.path.exists(dir_path):
            template_count = len([f for f in os.listdir(dir_path) if f.endswith('.html')])
            print(f"   ✅ {dir_path}: {template_count} قالب")
        else:
            print(f"   ⚠️ {dir_path}: غير موجود")
    
    print("\n✅ انتهى التشخيص!")
    
except ImportError as e:
    print(f"\n❌ خطأ في الاستيراد: {str(e)}")
    print("\n💡 تأكد من تثبيت المتطلبات:")
    print("   ./install_requirements.sh")
    
except Exception as e:
    print(f"\n❌ خطأ عام: {str(e)}")
    import traceback
    traceback.print_exc()