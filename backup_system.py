#!/usr/bin/env python3
"""
نظام النسخ الاحتياطي التلقائي
يحفظ نسخة من قاعدة البيانات بشكل دوري
"""
import os
import shutil
import datetime
import gzip
from pathlib import Path

class BackupManager:
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.max_backups = 30  # الاحتفاظ بآخر 30 نسخة
        
    def create_backup(self):
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # اسم الملف الأصلي
        db_file = "acc_light.db"
        if not os.path.exists(db_file):
            print(f"❌ Database file {db_file} not found!")
            return False
            
        # اسم النسخة الاحتياطية
        backup_name = f"backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_name
        
        try:
            # نسخ قاعدة البيانات
            shutil.copy2(db_file, backup_path)
            print(f"✅ Backup created: {backup_path}")
            
            # ضغط النسخة
            self._compress_backup(backup_path)
            
            # حذف النسخ القديمة
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def _compress_backup(self, backup_path):
        """ضغط النسخة الاحتياطية"""
        compressed_path = f"{backup_path}.gz"
        
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # حذف النسخة غير المضغوطة
        os.remove(backup_path)
        print(f"📦 Compressed: {compressed_path}")
    
    def _cleanup_old_backups(self):
        """حذف النسخ القديمة"""
        backups = sorted(self.backup_dir.glob("backup_*.db.gz"))
        
        if len(backups) > self.max_backups:
            for old_backup in backups[:-self.max_backups]:
                old_backup.unlink()
                print(f"🗑️ Deleted old backup: {old_backup.name}")
    
    def restore_backup(self, backup_name):
        """استرجاع نسخة احتياطية"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            print(f"❌ Backup {backup_name} not found!")
            return False
        
        try:
            # فك الضغط
            if backup_name.endswith('.gz'):
                with gzip.open(backup_path, 'rb') as f_in:
                    with open('acc_light.db.restore', 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                print(f"✅ Backup restored to: acc_light.db.restore")
                print("⚠️ Rename acc_light.db.restore to acc_light.db to use it")
            else:
                shutil.copy2(backup_path, 'acc_light.db.restore')
                
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    def list_backups(self):
        """عرض قائمة النسخ الاحتياطية"""
        backups = sorted(self.backup_dir.glob("backup_*.db.gz"), reverse=True)
        
        if not backups:
            print("📭 No backups found")
            return
        
        print(f"\n📚 Available backups ({len(backups)}):")
        print("-" * 50)
        
        for backup in backups[:10]:  # عرض آخر 10 نسخ
            size = backup.stat().st_size / 1024 / 1024  # MB
            date = datetime.datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"📦 {backup.name} ({size:.2f} MB) - {date.strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    import sys
    
    manager = BackupManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create":
            manager.create_backup()
        elif command == "list":
            manager.list_backups()
        elif command == "restore" and len(sys.argv) > 2:
            manager.restore_backup(sys.argv[2])
        else:
            print("Usage: python backup_system.py [create|list|restore <backup_name>]")
    else:
        # النسخ الاحتياطي التلقائي
        manager.create_backup()