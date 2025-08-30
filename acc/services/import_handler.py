"""
Universal Import Handler for CSV, Excel, and JSON files
"""
import csv
import json
import io
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple, Optional


class ImportHandler:
    """Enhanced import handler with multiple encoding support"""
    
    # Common encodings for Arabic content
    ENCODINGS = ['utf-8-sig', 'utf-8', 'windows-1256', 'iso-8859-1', 'cp1252', 'arabic']
    
    # Field mappings for different languages
    FIELD_MAPPINGS = {
        # Arabic mappings
        'الاسم': 'name',
        'الهاتف': 'phone',
        'البريد الإلكتروني': 'email',
        'البريد الالكتروني': 'email',
        'العنوان': 'address',
        'الرقم القومي': 'national_id',
        'الحالة': 'status',
        'الملاحظات': 'notes',
        'ملاحظات': 'notes',
        
        # English mappings
        'name': 'name',
        'phone': 'phone',
        'email': 'email',
        'address': 'address',
        'national_id': 'national_id',
        'national id': 'national_id',
        'status': 'status',
        'notes': 'notes',
        
        # Common variations
        'customer name': 'name',
        'customer_name': 'name',
        'اسم العميل': 'name',
        'رقم الهاتف': 'phone',
        'phone number': 'phone',
        'phone_number': 'phone',
    }
    
    @classmethod
    def detect_encoding(cls, file_content: bytes) -> str:
        """Detect file encoding by trying common encodings"""
        # Try BOM detection first
        if file_content.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig'
        elif file_content.startswith(b'\xff\xfe'):
            return 'utf-16-le'
        elif file_content.startswith(b'\xfe\xff'):
            return 'utf-16-be'
        
        # Try common encodings
        for encoding in cls.ENCODINGS:
            try:
                # Try to decode the entire content
                decoded = file_content.decode(encoding)
                # If successful, check for common Arabic characters
                if any('\u0600' <= char <= '\u06FF' for char in decoded[:1000]):
                    # Prefer windows-1256 for Arabic content if it works
                    if encoding == 'windows-1256':
                        return encoding
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        return 'utf-8'
    
    @classmethod
    def normalize_field_name(cls, field: str) -> str:
        """Normalize field names to match model attributes"""
        field = field.strip().lower()
        return cls.FIELD_MAPPINGS.get(field, field.replace(' ', '_'))
    
    @classmethod
    def import_csv(cls, file_content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Import CSV file with multiple encoding support"""
        errors = []
        data = []
        
        # Detect encoding
        encoding = cls.detect_encoding(file_content)
        
        try:
            # Decode content
            text_content = file_content.decode(encoding)
            
            # Use StringIO for CSV reading
            csv_file = io.StringIO(text_content)
            
            # Try different CSV dialects
            try:
                # First, try to detect the dialect
                sample = text_content[:1024]
                dialect = csv.Sniffer().sniff(sample)
                reader = csv.DictReader(csv_file, dialect=dialect)
            except:
                # Fall back to default dialect
                csv_file.seek(0)
                reader = csv.DictReader(csv_file)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Normalize field names
                    normalized_row = {}
                    for key, value in row.items():
                        if key:
                            normalized_key = cls.normalize_field_name(key)
                            normalized_row[normalized_key] = value.strip() if value else ''
                    
                    if normalized_row.get('name'):  # Ensure we have at least a name
                        data.append(normalized_row)
                    else:
                        errors.append(f"السطر {row_num}: الاسم مطلوب")
                        
                except Exception as e:
                    errors.append(f"السطر {row_num}: {str(e)}")
                    
        except Exception as e:
            errors.append(f"خطأ في قراءة الملف: {str(e)}")
        
        return data, errors
    
    @classmethod
    def import_excel(cls, file_content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Import Excel file (.xlsx) without external libraries"""
        errors = []
        data = []
        
        try:
            # Excel files are ZIP archives
            with zipfile.ZipFile(io.BytesIO(file_content)) as z:
                # Read shared strings
                shared_strings = []
                try:
                    with z.open('xl/sharedStrings.xml') as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
                            t = si.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')
                            shared_strings.append(t.text if t is not None and t.text else '')
                except:
                    pass
                
                # Read first worksheet
                with z.open('xl/worksheets/sheet1.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    
                    rows = []
                    for row in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                        cells = []
                        for c in row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                            v = c.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                            if v is not None and v.text:
                                # Check if it's a shared string
                                if c.get('t') == 's':
                                    try:
                                        cells.append(shared_strings[int(v.text)])
                                    except:
                                        cells.append(v.text)
                                else:
                                    cells.append(v.text)
                            else:
                                cells.append('')
                        
                        if cells:
                            rows.append(cells)
                    
                    # Process rows
                    if rows:
                        # First row is headers
                        headers = [cls.normalize_field_name(h) for h in rows[0]]
                        
                        # Process data rows
                        for row_num, row in enumerate(rows[1:], start=2):
                            try:
                                row_dict = {}
                                for i, value in enumerate(row):
                                    if i < len(headers):
                                        row_dict[headers[i]] = value
                                
                                if row_dict.get('name'):
                                    data.append(row_dict)
                                else:
                                    errors.append(f"السطر {row_num}: الاسم مطلوب")
                                    
                            except Exception as e:
                                errors.append(f"السطر {row_num}: {str(e)}")
                    
        except zipfile.BadZipFile:
            # Try as old Excel format (xls)
            errors.append("الملف ليس بتنسيق Excel صحيح (.xlsx). الرجاء استخدام Excel 2007 أو أحدث.")
        except Exception as e:
            errors.append(f"خطأ في قراءة ملف Excel: {str(e)}")
        
        return data, errors
    
    @classmethod
    def import_json(cls, file_content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Import JSON file with encoding support"""
        errors = []
        data = []
        
        # Detect encoding
        encoding = cls.detect_encoding(file_content)
        
        try:
            # Decode and parse JSON
            json_data = json.loads(file_content.decode(encoding))
            
            # Handle both array and object formats
            if isinstance(json_data, list):
                items = json_data
            elif isinstance(json_data, dict):
                # Try common keys for data arrays
                items = json_data.get('data', json_data.get('items', json_data.get('customers', [])))
                if not isinstance(items, list):
                    items = [json_data]
            else:
                items = []
            
            for idx, item in enumerate(items, start=1):
                try:
                    # Normalize field names
                    normalized_item = {}
                    for key, value in item.items():
                        normalized_key = cls.normalize_field_name(key)
                        normalized_item[normalized_key] = str(value).strip() if value else ''
                    
                    if normalized_item.get('name'):
                        data.append(normalized_item)
                    else:
                        errors.append(f"العنصر {idx}: الاسم مطلوب")
                        
                except Exception as e:
                    errors.append(f"العنصر {idx}: {str(e)}")
                    
        except json.JSONDecodeError as e:
            errors.append(f"خطأ في تحليل JSON: {str(e)}")
        except Exception as e:
            errors.append(f"خطأ في قراءة الملف: {str(e)}")
        
        return data, errors
    
    @classmethod
    def import_file(cls, file_content: bytes, filename: str) -> Tuple[List[Dict[str, Any]], List[str], str]:
        """
        Import file based on extension
        Returns: (data, errors, file_type)
        """
        filename_lower = filename.lower()
        
        if filename_lower.endswith('.csv'):
            data, errors = cls.import_csv(file_content)
            return data, errors, 'csv'
            
        elif filename_lower.endswith(('.xlsx', '.xls')):
            data, errors = cls.import_excel(file_content)
            return data, errors, 'excel'
            
        elif filename_lower.endswith('.json'):
            data, errors = cls.import_json(file_content)
            return data, errors, 'json'
            
        else:
            # Try to detect by content
            try:
                # Try JSON first
                data, errors = cls.import_json(file_content)
                if not errors:
                    return data, errors, 'json'
            except:
                pass
            
            # Try CSV
            try:
                data, errors = cls.import_csv(file_content)
                return data, errors, 'csv'
            except:
                pass
            
            return [], ["نوع الملف غير مدعوم. الرجاء استخدام CSV, Excel, أو JSON."], 'unknown'