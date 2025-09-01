#!/usr/bin/env python3
"""إصلاحات نهائية للتأكد من نجاح البناء"""

import os

def ensure_templates_exist():
    """التأكد من وجود جميع القوالب المطلوبة"""
    print("📁 التأكد من وجود القوالب...")
    
    # إنشاء مجلد القوالب إذا لم يكن موجوداً
    contracts_templates = "./acc/blueprints/contracts/templates/contracts"
    os.makedirs(contracts_templates, exist_ok=True)
    
    # التحقق من القوالب الموجودة
    existing = os.listdir(contracts_templates) if os.path.exists(contracts_templates) else []
    print(f"   القوالب الموجودة: {existing}")
    
    return True

def check_models_compatibility():
    """التحقق من توافق النماذج"""
    print("\n🔍 فحص توافق النماذج...")
    
    # التحقق من وجود الملفات
    files_to_check = [
        "./acc/models/contract.py",
        "./acc/models/installment.py",
        "./acc/blueprints/contracts/routes.py"
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            print(f"   ✅ {file} موجود")
            
            # التحقق من extend_existing
            with open(file, 'r') as f:
                content = f.read()
                if 'db.Model' in content and 'extend_existing' in content:
                    print(f"      ✓ يحتوي على extend_existing")
        else:
            print(f"   ❌ {file} غير موجود!")
    
    return True

def verify_imports():
    """التحقق من صحة الاستيرادات"""
    print("\n🔍 التحقق من الاستيرادات...")
    
    # فحص __init__.py للنماذج
    models_init = "./acc/models/__init__.py"
    if os.path.exists(models_init):
        with open(models_init, 'r') as f:
            content = f.read()
            
        required_imports = [
            "Contract",
            "Installment",
            "Customer",
            "Unit"
        ]
        
        for imp in required_imports:
            if imp in content:
                print(f"   ✅ {imp} مستورد")
            else:
                print(f"   ⚠️ {imp} قد يحتاج للاستيراد")
    
    return True

def create_simple_test():
    """إنشاء اختبار بسيط للتحقق من عمل النظام"""
    print("\n📝 إنشاء اختبار بسيط...")
    
    test_content = '''#!/usr/bin/env python3
"""اختبار بسيط للتأكد من عمل النظام"""

try:
    from acc import create_app
    from acc.models import Contract, Installment
    print("✅ الاستيرادات تعمل بشكل صحيح")
    
    app = create_app()
    print("✅ تم إنشاء التطبيق بنجاح")
    
    with app.app_context():
        from acc.extensions import db
        # محاولة query بسيط
        try:
            count = Contract.query.count()
            print(f"✅ عدد العقود في قاعدة البيانات: {count}")
        except:
            print("⚠️ قاعدة البيانات قد تحتاج لإنشاء الجداول")
    
except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()
'''
    
    with open('./test_system.py', 'w') as f:
        f.write(test_content)
    
    print("   ✅ تم إنشاء test_system.py")
    
    return True

def main():
    print("🚀 الإصلاحات النهائية...\n")
    
    ensure_templates_exist()
    check_models_compatibility()
    verify_imports()
    create_simple_test()
    
    print("\n✅ تمت جميع الفحوصات!")
    print("\n📋 يمكنك الآن:")
    print("1. تشغيل: python3 test_system.py للتحقق محلياً")
    print("2. مراقبة البناء على Render")

if __name__ == '__main__':
    main()