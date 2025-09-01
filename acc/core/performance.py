"""
نظام تحسين الأداء الموحد
"""
from functools import lru_cache, wraps
from datetime import datetime, timedelta
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

class PerformanceManager:
    """مدير الأداء الموحد"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.default_timeout = 300  # 5 دقائق
    
    def cached(self, timeout: int = None):
        """ديكوريتر للتخزين المؤقت"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
                
                # فحص التخزين المؤقت
                if cache_key in self.cache:
                    if datetime.now() - self.cache_timestamps[cache_key] < timedelta(seconds=timeout or self.default_timeout):
                        logger.debug(f"Cache hit for {func.__name__}")
                        return self.cache[cache_key]
                    else:
                        # انتهت صلاحية التخزين المؤقت
                        del self.cache[cache_key]
                        del self.cache_timestamps[cache_key]
                
                # تنفيذ الدالة وتخزين النتيجة
                result = func(*args, **kwargs)
                self.cache[cache_key] = result
                self.cache_timestamps[cache_key] = datetime.now()
                
                logger.debug(f"Cache miss for {func.__name__}, result cached")
                return result
            
            return wrapper
        return decorator
    
    def clear_cache(self, pattern: str = None):
        """مسح التخزين المؤقت"""
        if pattern:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
                del self.cache_timestamps[key]
            logger.info(f"Cleared {len(keys_to_remove)} cache entries matching '{pattern}'")
        else:
            self.cache.clear()
            self.cache_timestamps.clear()
            logger.info("Cleared all cache")
    
    def get_cache_stats(self):
        """إحصائيات التخزين المؤقت"""
        return {
            'total_entries': len(self.cache),
            'oldest_entry': min(self.cache_timestamps.values()) if self.cache_timestamps else None,
            'newest_entry': max(self.cache_timestamps.values()) if self.cache_timestamps else None
        }

# مثيل عام لمدير الأداء
performance_manager = PerformanceManager()

def optimize_query(query, limit: int = None):
    """تحسين الاستعلام"""
    if limit:
        query = query.limit(limit)
    return query

def bulk_operation(operation_func, items, batch_size: int = 100):
    """تنفيذ العمليات على دفعات"""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        result = operation_func(batch)
        results.append(result)
        logger.info(f"Processed batch {i//batch_size + 1}/{(len(items) + batch_size - 1)//batch_size}")
    return results

@lru_cache(maxsize=32)
def get_dashboard_stats_cached(project_id: str, cache_key: str):
    """إحصائيات لوحة التحكم مع تخزين مؤقت"""
    from acc.models import Contract, Unit, Voucher, Customer
    from acc.extensions import db
    from sqlalchemy import func
    
    stats = {}
    
    # إحصائيات العقود
    contract_stats = db.session.query(
        func.count(Contract.id).label('total'),
        func.sum(Contract.total_price).label('total_value'),
        Contract.status
    ).filter_by(project_id=project_id).group_by(Contract.status).all()
    
    stats['contracts'] = {
        'total': sum(s.total for s in contract_stats),
        'total_value': sum(s.total_value or 0 for s in contract_stats),
        'by_status': {s.status: s.total for s in contract_stats}
    }
    
    # إحصائيات الوحدات
    unit_stats = db.session.query(
        func.count(Unit.id).label('total'),
        Unit.status
    ).filter_by(project_id=project_id).group_by(Unit.status).all()
    
    stats['units'] = {
        'total': sum(s.total for s in unit_stats),
        'by_status': {s.status: s.total for s in unit_stats}
    }
    
    # إحصائيات مالية
    finance_stats = db.session.query(
        func.sum(Voucher.amount).label('total'),
        Voucher.type
    ).filter_by(project_id=project_id).group_by(Voucher.type).all()
    
    stats['finance'] = {
        'income': next((s.total for s in finance_stats if s.type == 'قبض'), 0) or 0,
        'expense': next((s.total for s in finance_stats if s.type == 'صرف'), 0) or 0
    }
    
    # إحصائيات العملاء
    stats['customers'] = db.session.query(func.count(Customer.id)).scalar() or 0
    
    return stats

def monitor_performance(func_name: str):
    """مراقبة أداء الدوال"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Function {func_name} executed in {execution_time:.3f} seconds")
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.error(f"Function {func_name} failed after {execution_time:.3f} seconds: {str(e)}")
                raise
        return wrapper
    return decorator