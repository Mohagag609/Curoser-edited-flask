"""
خدمة الـ Caching للنظام
Simple but effective caching service
"""
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import json

class CacheService:
    """خدمة cache بسيطة وفعالة"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self.default_timeout = 300  # 5 دقائق
        
    def _make_key(self, *args, **kwargs):
        """إنشاء مفتاح فريد للـ cache"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key):
        """جلب قيمة من الـ cache"""
        if key in self._cache:
            # التحقق من انتهاء الصلاحية
            if datetime.now() < self._timestamps[key]:
                return self._cache[key]
            else:
                # حذف القيمة المنتهية
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    def set(self, key, value, timeout=None):
        """حفظ قيمة في الـ cache"""
        timeout = timeout or self.default_timeout
        self._cache[key] = value
        self._timestamps[key] = datetime.now() + timedelta(seconds=timeout)
        return value
    
    def delete(self, key):
        """حذف قيمة من الـ cache"""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
    
    def clear(self):
        """مسح كل الـ cache"""
        self._cache.clear()
        self._timestamps.clear()
    
    def cleanup(self):
        """تنظيف القيم المنتهية"""
        now = datetime.now()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if timestamp < now
        ]
        for key in expired_keys:
            self.delete(key)
    
    def stats(self):
        """إحصائيات الـ cache"""
        self.cleanup()
        return {
            'total_items': len(self._cache),
            'memory_usage': sum(len(str(v)) for v in self._cache.values()),
            'oldest_item': min(self._timestamps.values()) if self._timestamps else None,
            'newest_item': max(self._timestamps.values()) if self._timestamps else None
        }

# Instance واحد للاستخدام في كل التطبيق
cache = CacheService()

def cached(timeout=None, key_prefix=''):
    """Decorator للـ caching"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # إنشاء cache key
            cache_key = f"{key_prefix}:{func.__name__}:{cache._make_key(*args, **kwargs)}"
            
            # محاولة جلب من cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # تنفيذ الدالة وحفظ النتيجة
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        # إضافة method لمسح cache هذه الدالة
        wrapper.clear_cache = lambda: cache.delete(
            f"{key_prefix}:{func.__name__}:*"
        )
        
        return wrapper
    return decorator

# أمثلة استخدام

@cached(timeout=600, key_prefix='customers')
def get_customer_stats(project_id):
    """إحصائيات العملاء مع cache لمدة 10 دقائق"""
    from acc.models import Customer, Contract
    from acc.extensions import db
    
    total = Customer.query.count()
    active = Contract.query.filter_by(
        project_id=project_id, 
        status='نشط'
    ).distinct(Contract.customer_id).count()
    
    return {
        'total': total,
        'active': active,
        'inactive': total - active
    }

@cached(timeout=300, key_prefix='units')
def get_available_units(project_id):
    """الوحدات المتاحة مع cache لمدة 5 دقائق"""
    from acc.models import Unit
    
    return Unit.query.filter_by(
        project_id=project_id,
        status='متاحة'
    ).all()

# Cache invalidation helpers
def invalidate_customer_cache():
    """مسح cache العملاء عند إضافة/تعديل/حذف"""
    cache.clear()  # أو يمكن مسح keys محددة

def invalidate_project_cache(project_id):
    """مسح cache مشروع معين"""
    # مسح كل keys الخاصة بالمشروع
    keys_to_delete = [
        k for k in cache._cache.keys() 
        if str(project_id) in k
    ]
    for key in keys_to_delete:
        cache.delete(key)