"""
نظام تسجيل الأحداث والتدقيق
Audit and Logging System
"""

from datetime import datetime
from flask import g, request
import json
import logging

# إعداد logger
logger = logging.getLogger(__name__)

def log_action(action_type, details=None, user_id=None):
    """
    تسجيل حدث في النظام
    
    Args:
        action_type (str): نوع الحدث (مثل: إنشاء عقد، حذف عقد، تعديل عميل)
        details (dict): تفاصيل إضافية عن الحدث
        user_id (str): معرف المستخدم (اختياري)
    """
    try:
        # الحصول على معرف المستخدم من السياق إذا لم يتم تمريره
        if not user_id and hasattr(g, 'user') and hasattr(g.user, 'id'):
            user_id = g.user.id
        
        # إعداد بيانات الحدث
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action_type,
            'user_id': user_id or 'system',
            'ip_address': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'details': details or {}
        }
        
        # تسجيل في ملف السجل
        logger.info(f"AUDIT: {json.dumps(audit_entry, ensure_ascii=False)}")
        
        # يمكن إضافة حفظ في قاعدة البيانات هنا في المستقبل
        # من خلال جدول audit_logs
        
        return True
        
    except Exception as e:
        logger.error(f"Error logging action: {str(e)}")
        return False

def get_user_actions(user_id, limit=50):
    """
    الحصول على آخر أحداث المستخدم
    
    Args:
        user_id (str): معرف المستخدم
        limit (int): عدد الأحداث المطلوبة
        
    Returns:
        list: قائمة بالأحداث
    """
    # TODO: implement fetching from database
    return []

def get_recent_actions(action_type=None, limit=100):
    """
    الحصول على آخر الأحداث في النظام
    
    Args:
        action_type (str): نوع الحدث (اختياري)
        limit (int): عدد الأحداث المطلوبة
        
    Returns:
        list: قائمة بالأحداث
    """
    # TODO: implement fetching from database
    return []

def log_error(error_message, error_type='general', details=None):
    """
    تسجيل خطأ في النظام
    
    Args:
        error_message (str): رسالة الخطأ
        error_type (str): نوع الخطأ
        details (dict): تفاصيل إضافية
    """
    try:
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': error_message,
            'user_id': g.user.id if hasattr(g, 'user') and hasattr(g.user, 'id') else None,
            'url': request.url if request else None,
            'method': request.method if request else None,
            'details': details or {}
        }
        
        logger.error(f"ERROR: {json.dumps(error_entry, ensure_ascii=False)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error logging error: {str(e)}")
        return False

# أحداث نموذجية للنظام
class AuditActions:
    """ثوابت لأنواع الأحداث"""
    
    # العقود
    CONTRACT_CREATE = "إنشاء عقد"
    CONTRACT_UPDATE = "تعديل عقد"
    CONTRACT_DELETE = "حذف عقد"
    CONTRACT_ACTIVATE = "تفعيل عقد"
    CONTRACT_CANCEL = "إلغاء عقد"
    
    # الأقساط
    INSTALLMENT_CREATE = "إنشاء قسط"
    INSTALLMENT_UPDATE = "تعديل قسط"
    INSTALLMENT_PAY = "دفع قسط"
    INSTALLMENT_CANCEL = "إلغاء قسط"
    
    # العملاء
    CUSTOMER_CREATE = "إضافة عميل"
    CUSTOMER_UPDATE = "تعديل عميل"
    CUSTOMER_DELETE = "حذف عميل"
    
    # الوحدات
    UNIT_CREATE = "إضافة وحدة"
    UNIT_UPDATE = "تعديل وحدة"
    UNIT_DELETE = "حذف وحدة"
    UNIT_RESERVE = "حجز وحدة"
    UNIT_RELEASE = "إلغاء حجز وحدة"
    
    # المالية
    PAYMENT_CREATE = "إضافة دفعة"
    PAYMENT_CANCEL = "إلغاء دفعة"
    VOUCHER_CREATE = "إنشاء سند"
    VOUCHER_APPROVE = "اعتماد سند"
    
    # النظام
    USER_LOGIN = "تسجيل دخول"
    USER_LOGOUT = "تسجيل خروج"
    BACKUP_CREATE = "إنشاء نسخة احتياطية"
    REPORT_GENERATE = "توليد تقرير"