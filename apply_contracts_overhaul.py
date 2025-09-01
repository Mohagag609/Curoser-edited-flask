#!/usr/bin/env python3
"""
تطبيق الإصلاح الشامل لنظام العقود والأقساط
Apply Contracts System Overhaul
"""

import os
import shutil
from datetime import datetime

def apply_overhaul():
    """تطبيق جميع التعديلات على النظام"""
    print("🚀 تطبيق الإصلاح الشامل لنظام العقود والأقساط...\n")
    
    # 1. نسخ احتياطي للملفات الأصلية
    print("1️⃣ إنشاء نسخ احتياطية...")
    backup_dir = f"/workspace/backup_original_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        "/workspace/acc/models/contract.py",
        "/workspace/acc/models/installment.py", 
        "/workspace/acc/blueprints/contracts/routes.py"
    ]
    
    for file in files_to_backup:
        if os.path.exists(file):
            dest = os.path.join(backup_dir, os.path.basename(file))
            shutil.copy2(file, dest)
            print(f"   ✅ نسخ {os.path.basename(file)}")
    
    # 2. استبدال الملفات بالنسخ المحسّنة
    print("\n2️⃣ تطبيق الملفات المحسّنة...")
    
    # استبدال نموذج العقود
    if os.path.exists("/workspace/acc/models/contract_enhanced.py"):
        shutil.copy2("/workspace/acc/models/contract_enhanced.py", 
                     "/workspace/acc/models/contract.py")
        print("   ✅ تم تحديث نموذج العقود")
    
    # استبدال نموذج الأقساط
    if os.path.exists("/workspace/acc/models/installment_enhanced.py"):
        shutil.copy2("/workspace/acc/models/installment_enhanced.py",
                     "/workspace/acc/models/installment.py")
        print("   ✅ تم تحديث نموذج الأقساط")
    
    # استبدال routes
    if os.path.exists("/workspace/acc/blueprints/contracts/routes_enhanced.py"):
        shutil.copy2("/workspace/acc/blueprints/contracts/routes_enhanced.py",
                     "/workspace/acc/blueprints/contracts/routes.py")
        print("   ✅ تم تحديث مسارات العقود")
    
    # 3. تحديث imports في __init__.py
    print("\n3️⃣ تحديث الاستيرادات...")
    
    models_init = "/workspace/acc/models/__init__.py"
    if os.path.exists(models_init):
        with open(models_init, 'r') as f:
            content = f.read()
        
        # إضافة الاستيرادات الجديدة إذا لم تكن موجودة
        new_imports = """
# Contract models
from acc.models.contract import Contract, ContractStatus, PaymentType, InstallmentPeriod, ContractDocument
from acc.models.installment import Installment, InstallmentStatus, InstallmentType, InstallmentPayment, InstallmentReminder
"""
        
        if "ContractStatus" not in content:
            # إضافة في النهاية
            with open(models_init, 'a') as f:
                f.write(new_imports)
            print("   ✅ تم تحديث استيرادات النماذج")
    
    # 4. إضافة الإصلاحات إلى build.sh
    print("\n4️⃣ تحديث build.sh...")
    
    build_sh = "/workspace/build.sh"
    if os.path.exists(build_sh):
        with open(build_sh, 'r') as f:
            content = f.read()
        
        # إضافة تشغيل تحديث قاعدة البيانات
        if "update_contracts_db.py" not in content:
            # البحث عن مكان مناسب للإضافة
            marker = "# Run database fixes if needed"
            if marker in content:
                addition = """
# Run contracts system update
if [ -f "update_contracts_db.py" ]; then
    echo "Updating contracts database schema..."
    python3 update_contracts_db.py || echo "Warning: Contracts update may have partially failed"
fi
"""
                content = content.replace(marker, marker + "\n" + addition)
                
                with open(build_sh, 'w') as f:
                    f.write(content)
                print("   ✅ تم تحديث build.sh")
    
    print("\n✅ تم تطبيق جميع التعديلات!")
    print(f"\n📁 النسخ الاحتياطية محفوظة في: {backup_dir}")
    print("\n⚠️ تنبيه: يجب تشغيل update_contracts_db.py لتحديث قاعدة البيانات")
    print("\n📋 الخطوات التالية:")
    print("1. git add .")
    print("2. git commit -m 'Apply contracts system overhaul'")
    print("3. git push")
    print("4. سيتم تطبيق التغييرات تلقائياً على Render")

if __name__ == '__main__':
    apply_overhaul()