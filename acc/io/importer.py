"""
محرك الاستيراد العام
"""
import csv
import io
from typing import List, Dict, Any, Tuple, Optional
from flask import g
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from acc.extensions import db
from acc.models import Project
from .schemas import get_schema, ResourceSchema
import pandas as pd

class ImportResult:
    """نتيجة عملية الاستيراد"""
    def __init__(self):
        self.inserted = 0
        self.updated = 0
        self.skipped_duplicates = 0
        self.errors: List[Dict[str, Any]] = []
        
    @property
    def total_processed(self):
        return self.inserted + self.updated + self.skipped_duplicates + len(self.errors)
    
    @property
    def success(self):
        return len(self.errors) == 0 or (self.inserted + self.updated > 0)
    
    def to_dict(self):
        return {
            'ok': self.success,
            'message': self.get_message(),
            'report': {
                'inserted': self.inserted,
                'updated': self.updated,
                'skipped_duplicates': self.skipped_duplicates,
                'errors': self.errors[:10]  # أول 10 أخطاء فقط
            }
        }
    
    def get_message(self):
        parts = []
        if self.inserted > 0:
            parts.append(f"تم الإدراج: {self.inserted}")
        if self.updated > 0:
            parts.append(f"تم التحديث: {self.updated}")
        if self.skipped_duplicates > 0:
            parts.append(f"مكرر: {self.skipped_duplicates}")
        if len(self.errors) > 0:
            parts.append(f"أخطاء: {len(self.errors)}")
        
        return " | ".join(parts) if parts else "لم يتم معالجة أي سجلات"

class GenericImporter:
    """مستورد عام للبيانات"""
    
    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        self.schema = get_schema(resource_name)
        if not self.schema:
            raise ValueError(f"مورد غير معرف: {resource_name}")
        
        self.model_class = self.schema.model_class
        self.current_project_id = g.current_project.id if hasattr(g, 'current_project') and g.current_project else None
    
    def import_file(self, file_content: bytes, filename: str, mode: str = 'insert') -> ImportResult:
        """استيراد ملف"""
        result = ImportResult()
        
        # تحديد نوع الملف
        file_ext = filename.lower().split('.')[-1]
        
        try:
            if file_ext == 'csv':
                df = self._read_csv(file_content)
            elif file_ext in ['xlsx', 'xls']:
                df = self._read_excel(file_content)
            else:
                result.errors.append({
                    'row': 0,
                    'error': f'صيغة ملف غير مدعومة: {file_ext}'
                })
                return result
        except Exception as e:
            result.errors.append({
                'row': 0,
                'error': f'خطأ في قراءة الملف: {str(e)}'
            })
            return result
        
        # معالجة البيانات
        return self._process_dataframe(df, mode, result)
    
    def _read_csv(self, content: bytes) -> pd.DataFrame:
        """قراءة ملف CSV"""
        # محاولة اكتشاف الترميز
        try:
            text = content.decode('utf-8-sig')
        except:
            try:
                text = content.decode('utf-8')
            except:
                text = content.decode('windows-1256')
        
        return pd.read_csv(io.StringIO(text))
    
    def _read_excel(self, content: bytes) -> pd.DataFrame:
        """قراءة ملف Excel"""
        return pd.read_excel(io.BytesIO(content), engine='openpyxl')
    
    def _process_dataframe(self, df: pd.DataFrame, mode: str, result: ImportResult) -> ImportResult:
        """معالجة DataFrame"""
        # توحيد أسماء الأعمدة
        df.columns = [col.strip().lower() for col in df.columns]
        
        # التحقق من الأعمدة المطلوبة
        missing_required = []
        for col in self.schema.required_columns:
            if col not in df.columns:
                missing_required.append(self.schema.column_map[col]['label'])
        
        if missing_required:
            result.errors.append({
                'row': 0,
                'error': f'أعمدة مطلوبة مفقودة: {", ".join(missing_required)}'
            })
            return result
        
        # تحميل السجلات الموجودة للمقارنة
        existing_records = self._load_existing_records()
        
        # معالجة كل صف
        for idx, row in df.iterrows():
            row_num = idx + 2  # رقم الصف في Excel (1-based + header)
            self._process_row(row, row_num, mode, existing_records, result)
        
        # حفظ التغييرات
        if result.success and (result.inserted > 0 or result.updated > 0):
            try:
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                result.errors.append({
                    'row': 0,
                    'error': 'تعارض في مفتاح فريد. تم إلغاء العملية.'
                })
                result.inserted = 0
                result.updated = 0
        
        return result
    
    def _load_existing_records(self) -> Dict[Tuple, Any]:
        """تحميل السجلات الموجودة"""
        query = self.model_class.query
        
        # إضافة فلتر المشروع إذا لزم الأمر
        if self._needs_project_filter():
            query = query.filter_by(project_id=self.current_project_id)
        
        records = {}
        for record in query.all():
            key = self._get_unique_key(record)
            if key:
                records[key] = record
        
        return records
    
    def _needs_project_filter(self) -> bool:
        """التحقق من الحاجة لفلتر المشروع"""
        return hasattr(self.model_class, 'project_id') and self.current_project_id
    
    def _get_unique_key(self, obj_or_row) -> Optional[Tuple]:
        """استخراج المفتاح الفريد"""
        values = []
        
        for field in self.schema.unique_by:
            if hasattr(obj_or_row, field):
                # كائن SQLAlchemy
                value = getattr(obj_or_row, field)
            elif isinstance(obj_or_row, (dict, pd.Series)):
                # صف من DataFrame
                value = obj_or_row.get(field)
            else:
                return None
            
            # معالجة خاصة لـ project_id
            if field == 'project_id' and value is None:
                value = self.current_project_id
            
            values.append(value)
        
        return tuple(values) if all(v is not None for v in values) else None
    
    def _process_row(self, row: pd.Series, row_num: int, mode: str, 
                     existing_records: Dict, result: ImportResult):
        """معالجة صف واحد"""
        # تطبيع البيانات
        normalized_data = {}
        errors = []
        
        for col_name, col_def in self.schema.column_map.items():
            if col_name in row and pd.notna(row[col_name]):
                value = row[col_name]
                
                # تطبيق دالة التطبيع
                if 'normalizer' in col_def:
                    try:
                        value = col_def['normalizer'](value)
                    except Exception as e:
                        errors.append(f"خطأ في تطبيع {col_def['label']}: {str(e)}")
                        continue
                
                # التحقق من القيم المسموحة
                if 'choices' in col_def and value and value not in col_def['choices']:
                    errors.append(f"{col_def['label']}: قيمة غير صالحة '{value}'")
                    continue
                
                normalized_data[col_name] = value
        
        # التحقق من الحقول المطلوبة
        for req_col in self.schema.required_columns:
            if req_col not in normalized_data or not normalized_data[req_col]:
                errors.append(f"{self.schema.column_map[req_col]['label']} مطلوب")
        
        if errors:
            result.errors.append({
                'row': row_num,
                'error': ' | '.join(errors)
            })
            return
        
        # معالجة العلاقات الخاصة
        self._process_relationships(normalized_data, row, errors)
        
        if errors:
            result.errors.append({
                'row': row_num,
                'error': ' | '.join(errors)
            })
            return
        
        # التحقق من التكرار
        unique_key = self._get_unique_key(normalized_data)
        existing = existing_records.get(unique_key) if unique_key else None
        
        if existing:
            if mode == 'insert':
                result.skipped_duplicates += 1
            else:  # upsert
                # تحديث الحقول غير الفارغة فقط
                updated = False
                for key, value in normalized_data.items():
                    if value and hasattr(existing, key):
                        old_value = getattr(existing, key)
                        if old_value != value:
                            setattr(existing, key, value)
                            updated = True
                
                if updated:
                    result.updated += 1
                else:
                    result.skipped_duplicates += 1
        else:
            # إنشاء سجل جديد
            try:
                new_obj = self.model_class(**normalized_data)
                
                # إضافة project_id إذا لزم الأمر
                if self._needs_project_filter():
                    new_obj.project_id = self.current_project_id
                
                # توليد الكود إذا لزم الأمر
                if hasattr(new_obj, 'generate_code') and not getattr(new_obj, 'code', None):
                    new_obj.generate_code()
                
                db.session.add(new_obj)
                result.inserted += 1
                
                # إضافة للسجلات الموجودة لتجنب التكرار في نفس الملف
                if unique_key:
                    existing_records[unique_key] = new_obj
                    
            except Exception as e:
                result.errors.append({
                    'row': row_num,
                    'error': f'خطأ في الإنشاء: {str(e)}'
                })
    
    def _process_relationships(self, data: Dict, row: pd.Series, errors: List[str]):
        """معالجة العلاقات (مثل المشروع، المورد)"""
        # معالجة كود المشروع للوحدات
        if self.resource_name == 'units' and 'project_code' in row:
            project_code = row.get('project_code')
            if project_code:
                project = Project.query.filter_by(code=project_code).first()
                if project:
                    data['project_id'] = project.id
                    data.pop('project_code', None)
                else:
                    errors.append(f"كود المشروع '{project_code}' غير موجود")
        
        # معالجة اسم المورد للمواد
        elif self.resource_name == 'materials' and 'supplier_name' in row:
            supplier_name = row.get('supplier_name')
            if supplier_name:
                from acc.models import Supplier
                supplier = Supplier.query.filter_by(name=supplier_name).first()
                if supplier:
                    data['supplier_id'] = supplier.id
                    data.pop('supplier_name', None)
                else:
                    errors.append(f"اسم المورد '{supplier_name}' غير موجود")