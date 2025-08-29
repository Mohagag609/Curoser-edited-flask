"""
Simple Excel import without pandas using csv module
"""
import csv
import io

def import_excel_as_csv(file):
    """
    قراءة ملف Excel البسيط كـ CSV
    ملاحظة: هذا يعمل مع ملفات Excel البسيطة المحفوظة كـ CSV
    """
    content = file.read()
    
    # محاولة فك الترميز بطرق مختلفة
    encodings = ['utf-8-sig', 'utf-8', 'windows-1256', 'iso-8859-1', 'cp1252']
    text = None
    
    for encoding in encodings:
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    
    if text is None:
        raise ValueError("لا يمكن قراءة الملف. يُرجى حفظ ملف Excel كـ CSV أولاً.")
    
    # البحث عن بداية البيانات (تخطي الأسطر الفارغة)
    lines = text.strip().split('\n')
    data_lines = []
    
    for line in lines:
        if line.strip():
            data_lines.append(line)
    
    if not data_lines:
        return []
    
    # قراءة البيانات
    reader = csv.DictReader(io.StringIO('\n'.join(data_lines)))
    
    customers_data = []
    for row in reader:
        # محاولة العثور على الأعمدة بأسماء مختلفة
        name = None
        for col in ['الاسم', 'Name', 'اسم العميل', 'Customer Name']:
            if col in row and row[col]:
                name = row[col].strip()
                break
        
        if not name:
            continue
        
        phone = None
        for col in ['الهاتف', 'Phone', 'رقم الهاتف', 'Mobile']:
            if col in row and row[col]:
                phone = row[col].strip()
                break
        
        national_id = None
        for col in ['الرقم القومي', 'National ID', 'ID', 'الهوية']:
            if col in row and row[col]:
                national_id = row[col].strip()
                break
        
        address = None
        for col in ['العنوان', 'Address', 'عنوان']:
            if col in row and row[col]:
                address = row[col].strip()
                break
        
        status = 'نشط'
        for col in ['الحالة', 'Status', 'حالة']:
            if col in row and row[col]:
                status = row[col].strip()
                break
        
        notes = None
        for col in ['ملاحظات', 'Notes', 'ملاحظة', 'Note']:
            if col in row and row[col]:
                notes = row[col].strip()
                break
        
        customers_data.append({
            'name': name,
            'phone': phone,
            'national_id': national_id,
            'address': address,
            'status': status if status else 'نشط',
            'notes': notes
        })
    
    return customers_data