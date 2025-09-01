"""
نظام النسخ الاحتياطي الموحد والمتقدم
"""
import os
import shutil
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class BackupManager:
    """مدير النسخ الاحتياطية"""
    
    def __init__(self, backup_dir: str = "backups", max_backups: int = 30):
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, db_path: str = "acc_light.db") -> bool:
        """إنشاء نسخة احتياطية"""
        if not os.path.exists(db_path):
            logger.error(f"Database file {db_path} not found!")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_name
        
        try:
            # نسخ قاعدة البيانات
            shutil.copy2(db_path, backup_path)
            logger.info(f"✅ Backup created: {backup_path}")
            
            # ضغط النسخة
            compressed_path = self._compress_backup(backup_path)
            
            # حذف النسخة غير المضغوطة
            backup_path.unlink()
            
            # إنشاء ملف معلومات النسخة
            self._create_backup_info(compressed_path)
            
            # تنظيف النسخ القديمة
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False
    
    def _compress_backup(self, backup_path: Path) -> Path:
        """ضغط النسخة الاحتياطية"""
        compressed_path = backup_path.with_suffix('.db.gz')
        
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        logger.info(f"✅ Backup compressed: {compressed_path}")
        return compressed_path
    
    def _create_backup_info(self, backup_path: Path):
        """إنشاء ملف معلومات النسخة"""
        info_path = backup_path.with_suffix('.info.json')
        info = {
            'created_at': datetime.now().isoformat(),
            'size': backup_path.stat().st_size,
            'type': 'database_backup',
            'version': '1.0'
        }
        
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
    
    def _cleanup_old_backups(self):
        """حذف النسخ القديمة"""
        backup_files = list(self.backup_dir.glob("backup_*.db.gz"))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if len(backup_files) > self.max_backups:
            files_to_delete = backup_files[self.max_backups:]
            for file_path in files_to_delete:
                file_path.unlink()
                # حذف ملف المعلومات أيضاً
                info_path = file_path.with_suffix('.info.json')
                if info_path.exists():
                    info_path.unlink()
                logger.info(f"🗑️ Deleted old backup: {file_path.name}")
    
    def list_backups(self) -> List[dict]:
        """قائمة النسخ الاحتياطية"""
        backups = []
        backup_files = list(self.backup_dir.glob("backup_*.db.gz"))
        
        for backup_file in backup_files:
            info_file = backup_file.with_suffix('.info.json')
            info = {}
            
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
            
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'size': backup_file.stat().st_size,
                'created_at': info.get('created_at', datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()),
                'size_mb': round(backup_file.stat().st_size / (1024 * 1024), 2)
            })
        
        return sorted(backups, key=lambda x: x['created_at'], reverse=True)
    
    def restore_backup(self, backup_filename: str, target_path: str = "acc_light.db") -> bool:
        """استعادة نسخة احتياطية"""
        backup_path = self.backup_dir / backup_filename
        
        if not backup_path.exists():
            logger.error(f"Backup file {backup_filename} not found!")
            return False
        
        try:
            # إنشاء نسخة احتياطية من الملف الحالي
            if os.path.exists(target_path):
                current_backup = f"{target_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(target_path, current_backup)
                logger.info(f"Current database backed up to: {current_backup}")
            
            # استعادة النسخة
            if backup_path.suffix == '.gz':
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(target_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(backup_path, target_path)
            
            logger.info(f"✅ Database restored from: {backup_filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False
    
    def get_backup_stats(self) -> dict:
        """إحصائيات النسخ الاحتياطية"""
        backups = self.list_backups()
        total_size = sum(backup['size'] for backup in backups)
        
        return {
            'total_backups': len(backups),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'oldest_backup': backups[-1]['created_at'] if backups else None,
            'newest_backup': backups[0]['created_at'] if backups else None,
            'max_backups': self.max_backups
        }

# مثيل عام لمدير النسخ الاحتياطية
backup_manager = BackupManager()

def create_automatic_backup():
    """إنشاء نسخة احتياطية تلقائية"""
    return backup_manager.create_backup()

def schedule_backups():
    """جدولة النسخ الاحتياطية (للاستخدام مع cron أو scheduler)"""
    # يمكن استخدام هذا مع APScheduler أو cron
    logger.info("🔄 Running scheduled backup...")
    success = create_automatic_backup()
    if success:
        logger.info("✅ Scheduled backup completed successfully")
    else:
        logger.error("❌ Scheduled backup failed")
    return success