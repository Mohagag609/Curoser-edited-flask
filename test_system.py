#!/usr/bin/env python3
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
