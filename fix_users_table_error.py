#!/usr/bin/env python3
"""إصلاح مشكلة جدول users المفقود"""

import os
import re

def remove_user_references():
    """إزالة المراجع إلى جدول users من النماذج"""
    print("🔧 إزالة المراجع إلى جدول users...")
    
    # الملفات التي تحتاج لإصلاح
    files_to_fix = [
        './acc/models/contract.py',
        './acc/models/installment.py'
    ]
    
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # إزالة foreign keys التي تشير إلى users
            content = re.sub(r"created_by = Column\(String\(20\), ForeignKey\('users\.id'\)\)", 
                           "created_by = Column(String(20))", content)
            content = re.sub(r"approved_by = Column\(String\(20\), ForeignKey\('users\.id'\)\)", 
                           "approved_by = Column(String(20))", content)
            content = re.sub(r"uploaded_by = Column\(String\(20\), ForeignKey\('users\.id'\)\)", 
                           "uploaded_by = Column(String(20))", content)
            content = re.sub(r"collected_by = Column\(String\(20\), ForeignKey\('users\.id'\)\)", 
                           "collected_by = Column(String(20))", content)
            
            # إزالة أي foreign key آخر يشير إلى users.id
            content = re.sub(r"ForeignKey\('users\.id'\)", "nullable=True", content)
            
            if content != original_content:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"  ✅ تم إصلاح {os.path.basename(filepath)}")

def create_simple_user_model():
    """إنشاء نموذج بسيط للمستخدمين"""
    print("\n📝 إنشاء نموذج بسيط للمستخدمين...")
    
    user_model = '''from acc.extensions import db
from sqlalchemy import Column, String, Boolean, DateTime, func

class User(db.Model):
    """نموذج المستخدمين البسيط"""
    __tablename__ = 'users'
    __table_args__ = {"extend_existing": True}
    
    id = Column(String(20), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    role = Column(String(20), default='user')  # user, admin, manager
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<User {self.username}>'
'''
    
    with open('./acc/models/user.py', 'w') as f:
        f.write(user_model)
    
    print("  ✅ تم إنشاء user.py")
    
    # إضافة الاستيراد في __init__.py
    models_init = './acc/models/__init__.py'
    if os.path.exists(models_init):
        with open(models_init, 'r') as f:
            content = f.read()
        
        if 'from acc.models.user import User' not in content:
            # إضافة في البداية
            lines = content.split('\n')
            lines.insert(1, 'from acc.models.user import User')
            content = '\n'.join(lines)
            
            with open(models_init, 'w') as f:
                f.write(content)
            print("  ✅ تم إضافة User إلى __init__.py")

def update_g_user():
    """تحديث g.user في الملفات"""
    print("\n🔧 تحديث استخدامات g.user...")
    
    # البحث عن الملفات التي تستخدم g.user
    files_to_check = [
        './acc/blueprints/contracts/routes.py',
        './acc/services/audit.py'
    ]
    
    for filepath in files_to_check:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            
            # استبدال g.user.id بقيمة افتراضية
            content = content.replace('g.user.id if hasattr(g, \'user\') else None', 
                                    '\'system\' if not hasattr(g, \'user\') else g.user.id')
            content = content.replace('created_by=g.user.id if hasattr(g, \'user\') else None',
                                    'created_by=\'system\'')
            
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"  ✅ تم تحديث {os.path.basename(filepath)}")

def main():
    print("🚀 إصلاح مشكلة جدول users...\n")
    
    remove_user_references()
    create_simple_user_model()
    update_g_user()
    
    print("\n✅ تم الإصلاح!")
    print("\n📌 ملاحظة: تم إنشاء نموذج بسيط للمستخدمين")
    print("يمكن تطويره لاحقاً لإضافة نظام مصادقة كامل")

if __name__ == '__main__':
    main()