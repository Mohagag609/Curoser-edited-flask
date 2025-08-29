"""
Simple Excel reader using xml parsing (no external dependencies)
"""
import xml.etree.ElementTree as ET
import zipfile
import io
import re

def read_excel_simple(file_content):
    """
    قراءة ملف Excel بشكل بسيط باستخدام XML
    """
    try:
        # Excel files are actually zip files
        try:
            zip_file = zipfile.ZipFile(io.BytesIO(file_content))
        except zipfile.BadZipFile:
            raise ValueError("الملف ليس ملف Excel صالح. يُرجى التأكد من أن الملف بصيغة .xlsx")
        
        # البحث عن ملف shared strings
        shared_strings = []
        if 'xl/sharedStrings.xml' in zip_file.namelist():
            shared_strings_xml = zip_file.read('xl/sharedStrings.xml')
            root = ET.fromstring(shared_strings_xml)
            for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                text = ''
                for t in si.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                    if t.text:
                        text += t.text
                shared_strings.append(text)
        
        # قراءة البيانات من أول ورقة
        sheet_xml = zip_file.read('xl/worksheets/sheet1.xml')
        root = ET.fromstring(sheet_xml)
        
        rows = []
        for row in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
            cells = []
            for cell in row.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                value = ''
                cell_type = cell.get('t')
                
                v_element = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                if v_element is not None and v_element.text:
                    if cell_type == 's':  # shared string
                        idx = int(v_element.text)
                        if idx < len(shared_strings):
                            value = shared_strings[idx]
                    else:
                        value = v_element.text
                
                cells.append(value)
            
            if cells:  # تخطي الصفوف الفارغة
                rows.append(cells)
        
        if not rows:
            return []
        
        # افتراض أن الصف الأول هو العناوين
        headers = rows[0]
        data = []
        
        for row in rows[1:]:
            if not any(row):  # تخطي الصفوف الفارغة
                continue
                
            row_dict = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    row_dict[header] = row[i]
                else:
                    row_dict[header] = ''
            
            data.append(row_dict)
        
        return data
        
    except Exception as e:
        # إذا فشلت قراءة Excel، نحاول كـ CSV
        raise ValueError(f"لا يمكن قراءة الملف كـ Excel: {str(e)}")

def parse_excel_data(data):
    """
    تحويل البيانات المقروءة إلى تنسيق العملاء
    """
    customers_data = []
    
    for row in data:
        # البحث عن الاسم بأسماء أعمدة مختلفة
        name = None
        for col in ['الاسم', 'Name', 'اسم العميل', 'Customer Name', 'الأسم']:
            if col in row and row[col]:
                name = str(row[col]).strip()
                break
        
        if not name:
            continue
        
        # البحث عن الهاتف
        phone = None
        for col in ['الهاتف', 'Phone', 'رقم الهاتف', 'Mobile', 'التليفون', 'الموبايل']:
            if col in row and row[col]:
                phone = str(row[col]).strip()
                break
        
        # البحث عن الرقم القومي
        national_id = None
        for col in ['الرقم القومي', 'National ID', 'ID', 'الهوية', 'رقم قومي']:
            if col in row and row[col]:
                national_id = str(row[col]).strip()
                break
        
        # البحث عن العنوان
        address = None
        for col in ['العنوان', 'Address', 'عنوان', 'العنوان الكامل']:
            if col in row and row[col]:
                address = str(row[col]).strip()
                break
        
        # البحث عن الحالة
        status = 'نشط'
        for col in ['الحالة', 'Status', 'حالة', 'الوضع']:
            if col in row and row[col]:
                status = str(row[col]).strip()
                break
        
        # البحث عن الملاحظات
        notes = None
        for col in ['ملاحظات', 'Notes', 'ملاحظة', 'Note', 'تعليق']:
            if col in row and row[col]:
                notes = str(row[col]).strip()
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