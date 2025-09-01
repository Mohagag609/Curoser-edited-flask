#!/usr/bin/env python3
"""إصلاح تعارض backref في العلاقات"""

import os
import re

def fix_contract_relationships():
    """إصلاح العلاقات في نموذج Contract"""
    print("🔧 إصلاح العلاقات في Contract...")
    
    contract_file = './acc/models/contract.py'
    if os.path.exists(contract_file):
        with open(contract_file, 'r') as f:
            content = f.read()
        
        # البحث عن العلاقة مع Project وتغيير backref
        content = re.sub(
            r"project = relationship\('Project', backref='contracts'\)",
            "project = relationship('Project', backref='contract_list')",
            content
        )
        
        # أو إذا كانت بدون backref صريح
        content = re.sub(
            r"project = relationship\('Project'\)",
            "project = relationship('Project', backref='contract_list', overlaps='contracts')",
            content
        )
        
        with open(contract_file, 'w') as f:
            f.write(content)
        print("  ✅ تم إصلاح contract.py")

def check_project_model():
    """التحقق من نموذج Project"""
    print("\n🔍 فحص نموذج Project...")
    
    project_file = './acc/models/project.py'
    if os.path.exists(project_file):
        with open(project_file, 'r') as f:
            content = f.read()
        
        # التحقق من وجود علاقة contracts
        if 'contracts = ' in content:
            print("  ⚠️ يوجد علاقة contracts في Project")
            # إضافة overlaps إذا لزم الأمر
            content = re.sub(
                r"contracts = db\.relationship\('Contract'([^)]*)\)",
                r"contracts = db.relationship('Contract'\1, overlaps='contract_list,project')",
                content
            )
            
            with open(project_file, 'w') as f:
                f.write(content)
            print("  ✅ تم إضافة overlaps")

def alternative_fix():
    """حل بديل - إزالة backref من Contract"""
    print("\n🔧 تطبيق حل بديل...")
    
    contract_file = './acc/models/contract.py'
    if os.path.exists(contract_file):
        with open(contract_file, 'r') as f:
            content = f.read()
        
        # إزالة backref تماماً من علاقة project
        content = re.sub(
            r"project = relationship\('Project'[^)]*\)",
            "project = relationship('Project', overlaps='contracts')",
            content
        )
        
        with open(contract_file, 'w') as f:
            f.write(content)
        print("  ✅ تم تحديث العلاقات")

def add_lazy_loading():
    """إضافة lazy loading للعلاقات"""
    print("\n🔧 إضافة lazy loading...")
    
    files_to_update = ['./acc/models/contract.py', './acc/models/project.py']
    
    for filepath in files_to_update:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            
            # إضافة lazy='dynamic' للعلاقات الكبيرة
            content = re.sub(
                r"(contracts = .*relationship\([^)]+)\)",
                r"\1, lazy='dynamic')",
                content
            )
            
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"  ✅ تم تحديث {os.path.basename(filepath)}")

def main():
    print("🚀 إصلاح تعارض backref...\n")
    
    fix_contract_relationships()
    check_project_model()
    alternative_fix()
    add_lazy_loading()
    
    print("\n✅ تم الإصلاح!")
    print("\n📌 الحلول المطبقة:")
    print("1. تغيير اسم backref لتجنب التعارض")
    print("2. إضافة overlaps للعلاقات المتداخلة")
    print("3. إضافة lazy loading لتحسين الأداء")

if __name__ == '__main__':
    main()