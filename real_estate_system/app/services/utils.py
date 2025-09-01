from datetime import datetime, date
from decimal import Decimal
import locale


def format_currency(amount, currency='ريال'):
    """تنسيق العملة"""
    if amount is None:
        return '0.00 ' + currency
    
    try:
        # تحويل إلى رقم عشري
        if isinstance(amount, str):
            amount = Decimal(amount)
        elif isinstance(amount, (int, float)):
            amount = Decimal(str(amount))
        
        # تنسيق الرقم
        formatted_amount = f"{amount:,.2f}"
        return f"{formatted_amount} {currency}"
    except (ValueError, TypeError):
        return '0.00 ' + currency


def format_date(date_obj, format_str='%Y-%m-%d'):
    """تنسيق التاريخ"""
    if date_obj is None:
        return ''
    
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except ValueError:
            return date_obj
    
    return date_obj.strftime(format_str)


def format_datetime(datetime_obj, format_str='%Y-%m-%d %H:%M'):
    """تنسيق التاريخ والوقت"""
    if datetime_obj is None:
        return ''
    
    if isinstance(datetime_obj, str):
        try:
            datetime_obj = datetime.strptime(datetime_obj, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return datetime_obj
    
    return datetime_obj.strftime(format_str)


def calculate_age(birth_date):
    """حساب العمر"""
    if birth_date is None:
        return None
    
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age


def generate_code(prefix, length=6):
    """توليد كود"""
    import random
    import string
    
    # توليد جزء عشوائي
    random_part = ''.join(random.choices(string.digits, k=length))
    return f"{prefix}{random_part}"


def validate_national_id(national_id):
    """التحقق من صحة الرقم القومي"""
    if not national_id or len(national_id) != 14:
        return False
    
    try:
        int(national_id)
        return True
    except ValueError:
        return False


def validate_phone(phone):
    """التحقق من صحة رقم الهاتف"""
    if not phone:
        return True  # الهاتف اختياري
    
    # إزالة المسافات والرموز
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    # التحقق من الطول (10-15 رقم)
    return 10 <= len(clean_phone) <= 15


def validate_email(email):
    """التحقق من صحة البريد الإلكتروني"""
    if not email:
        return True  # البريد الإلكتروني اختياري
    
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def calculate_percentage(part, total):
    """حساب النسبة المئوية"""
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def calculate_installment_amount(total_amount, down_payment, number_of_installments):
    """حساب مبلغ القسط"""
    if number_of_installments <= 0:
        return 0
    
    remaining_amount = total_amount - down_payment
    return round(remaining_amount / number_of_installments, 2)


def get_status_color(status):
    """الحصول على لون الحالة"""
    status_colors = {
        'نشط': 'green',
        'متاح': 'blue',
        'مباع': 'purple',
        'محجوز': 'yellow',
        'ملغي': 'red',
        'معلق': 'orange',
        'مدفوع': 'green',
        'متأخر': 'red',
        'مكتمل': 'green',
        'مستحق': 'orange'
    }
    return status_colors.get(status, 'gray')


def get_status_icon(status):
    """الحصول على أيقونة الحالة"""
    status_icons = {
        'نشط': 'check-circle',
        'متاح': 'circle',
        'مباع': 'check-circle-fill',
        'محجوز': 'clock',
        'ملغي': 'x-circle',
        'معلق': 'clock',
        'مدفوع': 'check-circle-fill',
        'متأخر': 'exclamation-triangle',
        'مكتمل': 'check-circle-fill',
        'مستحق': 'clock'
    }
    return status_icons.get(status, 'circle')


def paginate_query(query, page, per_page=20):
    """تقسيم النتائج إلى صفحات"""
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )


def get_current_date():
    """الحصول على التاريخ الحالي"""
    return date.today()


def get_current_datetime():
    """الحصول على التاريخ والوقت الحالي"""
    return datetime.now()


def safe_divide(numerator, denominator, default=0):
    """قسمة آمنة"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default


def clean_string(text):
    """تنظيف النص"""
    if not text:
        return ''
    
    # إزالة المسافات الزائدة
    text = ' '.join(text.split())
    
    # إزالة الرموز الخاصة
    import re
    text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)
    
    return text.strip()


def truncate_text(text, length=100):
    """تقصير النص"""
    if not text:
        return ''
    
    if len(text) <= length:
        return text
    
    return text[:length] + '...'


def is_valid_date(date_string, format_str='%Y-%m-%d'):
    """التحقق من صحة التاريخ"""
    try:
        datetime.strptime(date_string, format_str)
        return True
    except ValueError:
        return False


def convert_to_date(date_string, format_str='%Y-%m-%d'):
    """تحويل النص إلى تاريخ"""
    try:
        return datetime.strptime(date_string, format_str).date()
    except ValueError:
        return None


def convert_to_datetime(datetime_string, format_str='%Y-%m-%d %H:%M:%S'):
    """تحويل النص إلى تاريخ ووقت"""
    try:
        return datetime.strptime(datetime_string, format_str)
    except ValueError:
        return None