"""
Simple export/import functionality without pandas
"""
from flask import make_response
import json
import csv
import io
from datetime import datetime

def simple_export_json(customers):
    """تصدير العملاء إلى JSON"""
    data = [customer.to_dict() for customer in customers]
    response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

def simple_export_csv(customers):
    """تصدير العملاء إلى CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # العناوين
    writer.writerow(['الكود', 'الاسم', 'الهاتف', 'الرقم القومي', 'العنوان', 'الحالة', 'ملاحظات', 'تاريخ التسجيل'])
    
    # البيانات
    for customer in customers:
        writer.writerow([
            customer.id,
            customer.name,
            customer.phone or '',
            customer.national_id or '',
            customer.address or '',
            customer.status,
            customer.notes or '',
            customer.created_at.strftime('%Y-%m-%d') if customer.created_at else ''
        ])
    
    # إنشاء الاستجابة مع BOM لدعم العربية
    response = make_response('\ufeff' + output.getvalue())  # Add BOM
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    response.headers['Content-Disposition'] = f'attachment; filename=customers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return response

def simple_import_json(file):
    """استيراد العملاء من JSON"""
    data = json.loads(file.read().decode('utf-8'))
    return data

def simple_import_csv(file):
    """استيراد العملاء من CSV"""
    content = file.read()
    # محاولة فك الترميز
    try:
        text = content.decode('utf-8-sig')  # UTF-8 with BOM
    except:
        text = content.decode('utf-8')
    
    reader = csv.DictReader(io.StringIO(text))
    
    customers_data = []
    for row in reader:
        name = row.get('الاسم', '').strip()
        if name:
            customers_data.append({
                'name': name,
                'phone': row.get('الهاتف', '').strip() or None,
                'national_id': row.get('الرقم القومي', '').strip() or None,
                'address': row.get('العنوان', '').strip() or None,
                'status': row.get('الحالة', 'نشط').strip() or 'نشط',
                'notes': row.get('ملاحظات', '').strip() or None
            })
    
    return customers_data