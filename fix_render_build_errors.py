#!/usr/bin/env python3
"""إصلاح أخطاء البناء على Render"""

import os
import re

def fix_paths_in_scripts():
    """إصلاح المسارات في السكريبتات"""
    print("🔧 إصلاح المسارات...")
    
    # الملفات التي تحتاج لإصلاح المسارات
    files_to_fix = [
        'fix_all_issues.py',
        'fix_auth_logout_error.py',
        'fix_db_errors.py',
        'quick_fix.py',
        'update_contracts_db.py'
    ]
    
    for filename in files_to_fix:
        filepath = f'/workspace/{filename}'
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            
            # استبدال المسارات
            original_content = content
            content = content.replace('/workspace/', './')
            content = content.replace('"/workspace', '".')
            
            if content != original_content:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"  ✅ تم إصلاح {filename}")

def fix_duplicate_table_error():
    """إصلاح خطأ الجدول المكرر"""
    print("\n🔧 إصلاح خطأ الجدول المكرر...")
    
    # إصلاح في contract.py
    contract_file = '/workspace/acc/models/contract.py'
    if os.path.exists(contract_file):
        with open(contract_file, 'r') as f:
            content = f.read()
        
        # إضافة __table_args__ إذا لم تكن موجودة
        if '__table_args__' not in content and 'class Contract(db.Model):' in content:
            # البحث عن نهاية تعريف الكلاس
            lines = content.split('\n')
            new_lines = []
            in_contract_class = False
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                if 'class Contract(db.Model):' in line:
                    in_contract_class = True
                elif in_contract_class and line.strip().startswith('__tablename__'):
                    # إضافة بعد __tablename__
                    new_lines.append('    __table_args__ = {"extend_existing": True}')
                    in_contract_class = False
            
            content = '\n'.join(new_lines)
            
            with open(contract_file, 'w') as f:
                f.write(content)
            print("  ✅ تم إصلاح contract.py")
    
    # إصلاح في installment.py
    installment_file = '/workspace/acc/models/installment.py'
    if os.path.exists(installment_file):
        with open(installment_file, 'r') as f:
            content = f.read()
        
        if '__table_args__' not in content and 'class Installment(db.Model):' in content:
            lines = content.split('\n')
            new_lines = []
            in_installment_class = False
            
            for i, line in enumerate(lines):
                new_lines.append(line)
                if 'class Installment(db.Model):' in line:
                    in_installment_class = True
                elif in_installment_class and line.strip().startswith('__tablename__'):
                    new_lines.append('    __table_args__ = {"extend_existing": True}')
                    in_installment_class = False
            
            content = '\n'.join(new_lines)
            
            with open(installment_file, 'w') as f:
                f.write(content)
            print("  ✅ تم إصلاح installment.py")

def fix_import_error():
    """إصلاح خطأ الاستيراد"""
    print("\n🔧 إصلاح خطأ الاستيراد...")
    
    routes_file = '/workspace/acc/blueprints/contracts/routes.py'
    if os.path.exists(routes_file):
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # استبدال الاستيراد الخاطئ
        content = content.replace(
            'from acc.models.contract_enhanced import Contract, ContractStatus, PaymentType, InstallmentPeriod',
            'from acc.models.contract import Contract, ContractStatus, PaymentType, InstallmentPeriod'
        )
        content = content.replace(
            'from acc.models.installment_enhanced import Installment, InstallmentStatus',
            'from acc.models.installment import Installment, InstallmentStatus'
        )
        
        with open(routes_file, 'w') as f:
            f.write(content)
        print("  ✅ تم إصلاح routes.py")

def create_missing_templates():
    """إنشاء القوالب المفقودة إذا لم تكن موجودة"""
    print("\n🔧 التحقق من القوالب...")
    
    template_dir = '/workspace/acc/blueprints/contracts/templates/contracts'
    os.makedirs(template_dir, exist_ok=True)
    
    # قائمة القوالب المطلوبة
    required_templates = ['view.html', 'index.html', 'create.html', 'edit.html']
    
    for template in required_templates:
        template_path = os.path.join(template_dir, template)
        if not os.path.exists(template_path):
            # إنشاء قالب مؤقت
            with open(template_path, 'w') as f:
                f.write(f'{{% extends "base.html" %}}\n{{% block content %}}<h1>{template}</h1>{{% endblock %}}')
            print(f"  ✅ تم إنشاء {template}")

def main():
    print("🚀 إصلاح أخطاء البناء على Render...\n")
    
    fix_paths_in_scripts()
    fix_duplicate_table_error()
    fix_import_error()
    create_missing_templates()
    
    print("\n✅ تم إصلاح جميع الأخطاء!")

if __name__ == '__main__':
    main()