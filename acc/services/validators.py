"""
Validators for input validation
"""
import re
from decimal import Decimal, InvalidOperation

def validate_phone(phone):
    """التحقق من صحة رقم الهاتف"""
    if not phone:
        return True  # الهاتف اختياري
    
    # إزالة المسافات والشرطات
    phone = phone.replace(" ", "").replace("-", "")
    
    # التحقق من الطول والأرقام فقط
    if not phone.isdigit():
        return False
    
    # أرقام الهاتف المصرية تبدأ بـ 01 وطولها 11 رقم
    # أو أرقام دولية تبدأ بـ + وطولها بين 10-15 رقم
    if phone.startswith("01") and len(phone) == 11:
        return True
    elif phone.startswith("+") and 10 <= len(phone[1:]) <= 15 and phone[1:].isdigit():
        return True
    elif 10 <= len(phone) <= 15:  # أرقام عامة
        return True
    
    return False

def validate_national_id(national_id):
    """التحقق من صحة الرقم القومي"""
    if not national_id:
        return True  # الرقم القومي اختياري
    
    # الرقم القومي المصري 14 رقم
    if not national_id.isdigit() or len(national_id) != 14:
        return False
    
    # التحقق من صحة التاريخ في الرقم القومي
    # الأرقام 1-7 تمثل التاريخ
    century = national_id[0]
    year = national_id[1:3]
    month = national_id[3:5]
    day = national_id[5:7]
    
    # التحقق من القرن
    if century not in ['2', '3']:  # 2 للقرن 20، 3 للقرن 21
        return False
    
    # التحقق من الشهر
    if not (1 <= int(month) <= 12):
        return False
    
    # التحقق من اليوم
    if not (1 <= int(day) <= 31):
        return False
    
    return True

def validate_email(email):
    """التحقق من صحة البريد الإلكتروني"""
    if not email:
        return True  # البريد الإلكتروني اختياري
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_amount(amount):
    """التحقق من صحة المبلغ"""
    try:
        decimal_amount = Decimal(str(amount))
        # التحقق من أن المبلغ موجب
        if decimal_amount < 0:
            return False, "المبلغ يجب أن يكون موجباً"
        
        # التحقق من عدد الخانات العشرية (حد أقصى 2)
        if decimal_amount.as_tuple().exponent < -2:
            return False, "المبلغ يحتوي على أكثر من خانتين عشريتين"
        
        # التحقق من الحد الأقصى (مليار)
        if decimal_amount > 1000000000:
            return False, "المبلغ كبير جداً"
        
        return True, None
    except (InvalidOperation, ValueError):
        return False, "مبلغ غير صحيح"

def validate_percentage(percentage):
    """التحقق من صحة النسبة المئوية"""
    try:
        decimal_percentage = Decimal(str(percentage))
        
        if not (0 <= decimal_percentage <= 100):
            return False, "النسبة يجب أن تكون بين 0 و 100"
        
        return True, None
    except (InvalidOperation, ValueError):
        return False, "نسبة غير صحيحة"

def validate_date_range(start_date, end_date):
    """التحقق من صحة نطاق التاريخ"""
    if not start_date or not end_date:
        return True, None  # التواريخ اختيارية
    
    if start_date > end_date:
        return False, "تاريخ البداية يجب أن يكون قبل تاريخ النهاية"
    
    return True, None

def validate_name(name, min_length=3, max_length=200):
    """التحقق من صحة الاسم"""
    if not name or not name.strip():
        return False, "الاسم مطلوب"
    
    name = name.strip()
    
    if len(name) < min_length:
        return False, f"الاسم قصير جداً (الحد الأدنى {min_length} أحرف)"
    
    if len(name) > max_length:
        return False, f"الاسم طويل جداً (الحد الأقصى {max_length} حرف)"
    
    # التحقق من عدم وجود أحرف خاصة ضارة
    if re.search(r'[<>\"\'%;()&+]', name):
        return False, "الاسم يحتوي على أحرف غير مسموحة"
    
    return True, None

def sanitize_text(text, max_length=None):
    """تنظيف النص من الأكواد الضارة"""
    if not text:
        return text
    
    # إزالة HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # إزالة multiple spaces
    text = ' '.join(text.split())
    
    # قص النص إذا كان طويلاً
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()