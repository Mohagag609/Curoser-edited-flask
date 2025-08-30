"""
تعريفات الموارد والحقول للاستيراد/التصدير
"""
from typing import Dict, List, Any, Callable, Optional
from acc.models import Customer, Supplier, Partner, Contractor, Broker, Unit, Material, Project

# دوال التطبيع
def normalize_name(value: str) -> str:
    """تطبيع الأسماء: تشذيب وتوحيد المسافات"""
    if not value:
        return ''
    # تشذيب وتوحيد المسافات المتعددة
    return ' '.join(value.strip().split())

def normalize_phone(value: str) -> str:
    """تطبيع أرقام الهاتف المصرية"""
    if not value:
        return ''
    
    # تحويل الأرقام العربية إلى إنجليزية
    arabic_to_english = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    for ar, en in arabic_to_english.items():
        value = value.replace(ar, en)
    
    # إزالة كل شيء عدا الأرقام
    phone = ''.join(c for c in value if c.isdigit())
    
    # معالجة أكواد مصر
    if phone.startswith('20') and len(phone) > 10:
        phone = '0' + phone[2:]
    elif phone.startswith('002') and len(phone) > 12:
        phone = phone[3:]
    elif phone.startswith('+20'):
        phone = '0' + phone[3:]
    
    return phone

def normalize_email(value: str) -> str:
    """تطبيع البريد الإلكتروني"""
    if not value:
        return ''
    return value.strip().lower()

def normalize_text(value: str) -> str:
    """تطبيع النص العادي"""
    if not value:
        return ''
    return value.strip()

def normalize_number(value: Any) -> Optional[float]:
    """تطبيع الأرقام"""
    if not value:
        return None
    try:
        # تحويل الأرقام العربية
        if isinstance(value, str):
            arabic_to_english = {
                '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
                '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
            }
            for ar, en in arabic_to_english.items():
                value = value.replace(ar, en)
        return float(value)
    except (ValueError, TypeError):
        return None

def normalize_percentage(value: Any) -> Optional[float]:
    """تطبيع النسب المئوية"""
    if not value:
        return None
    try:
        # إزالة علامة %
        if isinstance(value, str):
            value = value.replace('%', '').strip()
        return normalize_number(value)
    except:
        return None

# تعريف الحقول لكل مورد
class ResourceSchema:
    def __init__(self, 
                 model_class,
                 columns: List[Dict[str, Any]],
                 unique_by: List[str],
                 display_name: str,
                 plural_name: str):
        self.model_class = model_class
        self.columns = columns
        self.unique_by = unique_by
        self.display_name = display_name
        self.plural_name = plural_name
        
        # بناء خريطة الأعمدة للوصول السريع
        self.column_map = {col['name']: col for col in columns}
        
        # استخراج أسماء الأعمدة المطلوبة
        self.required_columns = [col['name'] for col in columns if col.get('required', False)]
        
        # استخراج أسماء جميع الأعمدة
        self.all_columns = [col['name'] for col in columns]

# تعريفات الموارد
SCHEMAS: Dict[str, ResourceSchema] = {
    'customers': ResourceSchema(
        model_class=Customer,
        display_name='عميل',
        plural_name='العملاء',
        unique_by=['name', 'phone'],
        columns=[
            {
                'name': 'name',
                'label': 'الاسم',
                'required': True,
                'normalizer': normalize_name,
                'example': 'أحمد محمد علي'
            },
            {
                'name': 'phone',
                'label': 'رقم الهاتف',
                'required': True,
                'normalizer': normalize_phone,
                'example': '01012345678'
            },
            {
                'name': 'phone2',
                'label': 'رقم هاتف آخر',
                'required': False,
                'normalizer': normalize_phone,
                'example': '01123456789'
            },
            {
                'name': 'national_id',
                'label': 'الرقم القومي',
                'required': False,
                'normalizer': normalize_text,
                'example': '29901011234567'
            },
            {
                'name': 'email',
                'label': 'البريد الإلكتروني',
                'required': False,
                'normalizer': normalize_email,
                'example': 'ahmed@example.com'
            },
            {
                'name': 'address',
                'label': 'العنوان',
                'required': False,
                'normalizer': normalize_text,
                'example': '15 شارع التحرير، القاهرة'
            },
            {
                'name': 'notes',
                'label': 'ملاحظات',
                'required': False,
                'normalizer': normalize_text,
                'example': 'عميل مميز'
            }
        ]
    ),
    
    'suppliers': ResourceSchema(
        model_class=Supplier,
        display_name='مورد',
        plural_name='الموردين',
        unique_by=['name'],
        columns=[
            {
                'name': 'name',
                'label': 'اسم المورد',
                'required': True,
                'normalizer': normalize_name,
                'example': 'شركة الأمل للتوريدات'
            },
            {
                'name': 'contact_person',
                'label': 'اسم المسؤول',
                'required': False,
                'normalizer': normalize_name,
                'example': 'محمد أحمد'
            },
            {
                'name': 'phone',
                'label': 'رقم الهاتف',
                'required': False,
                'normalizer': normalize_phone,
                'example': '01098765432'
            },
            {
                'name': 'email',
                'label': 'البريد الإلكتروني',
                'required': False,
                'normalizer': normalize_email,
                'example': 'info@alamal.com'
            },
            {
                'name': 'address',
                'label': 'العنوان',
                'required': False,
                'normalizer': normalize_text,
                'example': 'المنطقة الصناعية، 6 أكتوبر'
            },
            {
                'name': 'tax_number',
                'label': 'الرقم الضريبي',
                'required': False,
                'normalizer': normalize_text,
                'example': '123-456-789'
            },
            {
                'name': 'notes',
                'label': 'ملاحظات',
                'required': False,
                'normalizer': normalize_text,
                'example': 'يوفر خصومات للكميات الكبيرة'
            }
        ]
    ),
    
    'partners': ResourceSchema(
        model_class=Partner,
        display_name='شريك',
        plural_name='الشركاء',
        unique_by=['name'],
        columns=[
            {
                'name': 'name',
                'label': 'اسم الشريك',
                'required': True,
                'normalizer': normalize_name,
                'example': 'خالد السيد'
            },
            {
                'name': 'percentage',
                'label': 'نسبة الشراكة %',
                'required': True,
                'normalizer': normalize_percentage,
                'example': '25'
            },
            {
                'name': 'phone',
                'label': 'رقم الهاتف',
                'required': False,
                'normalizer': normalize_phone,
                'example': '01234567890'
            },
            {
                'name': 'email',
                'label': 'البريد الإلكتروني',
                'required': False,
                'normalizer': normalize_email,
                'example': 'khaled@example.com'
            },
            {
                'name': 'national_id',
                'label': 'الرقم القومي',
                'required': False,
                'normalizer': normalize_text,
                'example': '29801011234567'
            },
            {
                'name': 'address',
                'label': 'العنوان',
                'required': False,
                'normalizer': normalize_text,
                'example': 'المعادي، القاهرة'
            }
        ]
    ),
    
    'contractors': ResourceSchema(
        model_class=Contractor,
        display_name='مقاول',
        plural_name='المقاولين',
        unique_by=['name'],
        columns=[
            {
                'name': 'name',
                'label': 'اسم المقاول',
                'required': True,
                'normalizer': normalize_name,
                'example': 'مؤسسة النجاح للمقاولات'
            },
            {
                'name': 'contact_person',
                'label': 'اسم المسؤول',
                'required': False,
                'normalizer': normalize_name,
                'example': 'عبد الله حسن'
            },
            {
                'name': 'phone',
                'label': 'رقم الهاتف',
                'required': False,
                'normalizer': normalize_phone,
                'example': '01555666777'
            },
            {
                'name': 'specialization',
                'label': 'التخصص',
                'required': False,
                'normalizer': normalize_text,
                'example': 'أعمال التشطيبات'
            },
            {
                'name': 'email',
                'label': 'البريد الإلكتروني',
                'required': False,
                'normalizer': normalize_email,
                'example': 'info@najah.com'
            },
            {
                'name': 'address',
                'label': 'العنوان',
                'required': False,
                'normalizer': normalize_text,
                'example': 'مدينة نصر، القاهرة'
            }
        ]
    ),
    
    'brokers': ResourceSchema(
        model_class=Broker,
        display_name='وسيط',
        plural_name='الوسطاء',
        unique_by=['name', 'phone'],
        columns=[
            {
                'name': 'name',
                'label': 'اسم الوسيط',
                'required': True,
                'normalizer': normalize_name,
                'example': 'سامي فؤاد'
            },
            {
                'name': 'phone',
                'label': 'رقم الهاتف',
                'required': True,
                'normalizer': normalize_phone,
                'example': '01011223344'
            },
            {
                'name': 'commission_percentage',
                'label': 'نسبة العمولة %',
                'required': False,
                'normalizer': normalize_percentage,
                'example': '2.5'
            },
            {
                'name': 'email',
                'label': 'البريد الإلكتروني',
                'required': False,
                'normalizer': normalize_email,
                'example': 'sami@example.com'
            },
            {
                'name': 'address',
                'label': 'العنوان',
                'required': False,
                'normalizer': normalize_text,
                'example': 'الهرم، الجيزة'
            }
        ]
    ),
    
    'units': ResourceSchema(
        model_class=Unit,
        display_name='وحدة',
        plural_name='الوحدات',
        unique_by=['unit_number', 'project_id'],
        columns=[
            {
                'name': 'unit_number',
                'label': 'رقم الوحدة',
                'required': True,
                'normalizer': normalize_text,
                'example': 'A101'
            },
            {
                'name': 'project_code',
                'label': 'كود المشروع',
                'required': True,
                'normalizer': normalize_text,
                'example': 'PROJ001',
                'note': 'يجب أن يكون المشروع موجوداً مسبقاً'
            },
            {
                'name': 'type',
                'label': 'النوع',
                'required': False,
                'normalizer': normalize_text,
                'example': 'شقة'
            },
            {
                'name': 'floor',
                'label': 'الطابق',
                'required': False,
                'normalizer': normalize_text,
                'example': '3'
            },
            {
                'name': 'area',
                'label': 'المساحة',
                'required': False,
                'normalizer': normalize_number,
                'example': '150'
            },
            {
                'name': 'price',
                'label': 'السعر',
                'required': False,
                'normalizer': normalize_number,
                'example': '1500000'
            },
            {
                'name': 'status',
                'label': 'الحالة',
                'required': False,
                'normalizer': normalize_text,
                'example': 'متاحة',
                'choices': ['متاحة', 'محجوزة', 'مباعة']
            }
        ]
    ),
    
    'materials': ResourceSchema(
        model_class=Material,
        display_name='مادة',
        plural_name='المواد',
        unique_by=['name'],
        columns=[
            {
                'name': 'name',
                'label': 'اسم المادة',
                'required': True,
                'normalizer': normalize_name,
                'example': 'أسمنت بورتلاندي'
            },
            {
                'name': 'unit',
                'label': 'الوحدة',
                'required': False,
                'normalizer': normalize_text,
                'example': 'طن'
            },
            {
                'name': 'price',
                'label': 'السعر',
                'required': False,
                'normalizer': normalize_number,
                'example': '1200'
            },
            {
                'name': 'supplier_name',
                'label': 'اسم المورد',
                'required': False,
                'normalizer': normalize_name,
                'example': 'شركة الأمل للتوريدات',
                'note': 'يجب أن يكون المورد موجوداً مسبقاً'
            },
            {
                'name': 'description',
                'label': 'الوصف',
                'required': False,
                'normalizer': normalize_text,
                'example': 'أسمنت عالي الجودة'
            }
        ]
    ),
    
    'projects': ResourceSchema(
        model_class=Project,
        display_name='مشروع',
        plural_name='المشاريع',
        unique_by=['name'],
        columns=[
            {
                'name': 'name',
                'label': 'اسم المشروع',
                'required': True,
                'normalizer': normalize_name,
                'example': 'مشروع النخيل السكني'
            },
            {
                'name': 'code',
                'label': 'كود المشروع',
                'required': False,
                'normalizer': normalize_text,
                'example': 'PROJ001'
            },
            {
                'name': 'location',
                'label': 'الموقع',
                'required': False,
                'normalizer': normalize_text,
                'example': '6 أكتوبر، الجيزة'
            },
            {
                'name': 'start_date',
                'label': 'تاريخ البداية',
                'required': False,
                'normalizer': normalize_text,
                'example': '2024-01-01'
            },
            {
                'name': 'status',
                'label': 'الحالة',
                'required': False,
                'normalizer': normalize_text,
                'example': 'قيد التنفيذ',
                'choices': ['قيد التخطيط', 'قيد التنفيذ', 'مكتمل', 'متوقف']
            },
            {
                'name': 'description',
                'label': 'الوصف',
                'required': False,
                'normalizer': normalize_text,
                'example': 'مشروع سكني متكامل'
            }
        ]
    )
}

def get_schema(resource_name: str) -> Optional[ResourceSchema]:
    """الحصول على سكيما المورد"""
    return SCHEMAS.get(resource_name)

def list_resources() -> List[Dict[str, str]]:
    """قائمة الموارد المتاحة"""
    return [
        {
            'name': name,
            'display_name': schema.display_name,
            'plural_name': schema.plural_name
        }
        for name, schema in SCHEMAS.items()
    ]