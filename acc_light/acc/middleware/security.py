from functools import wraps
from flask import request, abort, current_app
import re

def sanitize_input(text):
    """تنظيف المدخلات من أي كود ضار"""
    if not text:
        return text
    
    # إزالة أي HTML/JS tags
    text = re.sub(r'<[^>]*>', '', str(text))
    
    # إزالة أي أكواد SQL injection شائعة
    dangerous_patterns = [
        r"';",
        r'";',
        r'--',
        r'/\*',
        r'\*/',
        r'xp_',
        r'sp_',
        r'exec\s+',
        r'execute\s+',
        r'select\s+.*\s+from',
        r'insert\s+into',
        r'delete\s+from',
        r'drop\s+',
        r'update\s+.*\s+set',
        r'union\s+',
        r'script',
        r'javascript:',
        r'onerror',
        r'onload',
        r'onclick',
        r'<iframe',
        r'<object',
        r'<embed'
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()

def rate_limit(max_requests=60, window=60):
    """حد أقصى للطلبات لمنع DDoS"""
    def decorator(f):
        requests = {}
        
        @wraps(f)
        def wrapped(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = int(time.time())
            
            # تنظيف الطلبات القديمة
            requests[client_ip] = [t for t in requests.get(client_ip, []) 
                                 if current_time - t < window]
            
            # التحقق من الحد الأقصى
            if len(requests.get(client_ip, [])) >= max_requests:
                abort(429)  # Too Many Requests
            
            # إضافة الطلب الحالي
            requests.setdefault(client_ip, []).append(current_time)
            
            return f(*args, **kwargs)
        
        return wrapped
    return decorator

def validate_file_upload(file):
    """التحقق من أمان رفع الملفات"""
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'json', 'pdf', 'png', 'jpg', 'jpeg'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    if not file:
        return False, "لم يتم اختيار ملف"
    
    # التحقق من الامتداد
    filename = file.filename.lower()
    if '.' not in filename:
        return False, "الملف بدون امتداد"
    
    ext = filename.rsplit('.', 1)[1]
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"نوع الملف غير مسموح. الأنواع المسموحة: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # التحقق من حجم الملف
    file.seek(0, 2)  # الذهاب لنهاية الملف
    size = file.tell()
    file.seek(0)  # العودة للبداية
    
    if size > MAX_FILE_SIZE:
        return False, f"حجم الملف كبير جداً. الحد الأقصى: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    # التحقق من محتوى الملف
    header = file.read(512)
    file.seek(0)
    
    # التحقق من executable files
    if header.startswith(b'MZ') or header.startswith(b'\x7fELF'):
        return False, "الملف قد يكون ملف تنفيذي"
    
    return True, None

import time