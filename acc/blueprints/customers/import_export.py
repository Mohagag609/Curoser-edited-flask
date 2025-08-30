"""
Customer Import/Export Handler using the new V2 system
معالج استيراد وتصدير العملاء باستخدام النظام الجديد V2
"""
from flask import request, jsonify, render_template
from acc.blueprints.customers import bp
from acc.extensions import db
from acc.models import Customer
from acc.services.import_export_v2 import UniversalImportExport, ImportResult
from acc.services.utils import generate_uid, log_action
from acc.services.code_generator import generate_customer_code
import pandas as pd
from datetime import datetime


# إنشاء معالج مخصص للعملاء
class CustomerImportExport(UniversalImportExport):
    """معالج مخصص للعملاء مع منطق خاص"""
    
    @classmethod
    def prepare_export_data(cls, customers):
        """تحضير بيانات العملاء للتصدير"""
        data = []
        for customer in customers:
            data.append({
                'code': customer.code,
                'name': customer.name,
                'phone': customer.phone or '',
                'email': customer.email or '',
                'national_id': customer.national_id or '',
                'address': customer.address or '',
                'status': customer.status,
                'notes': customer.notes or '',
                'created_at': customer.created_at
            })
        return data
    
    @classmethod
    def validate_customer_data(cls, df):
        """تحقق إضافي خاص بالعملاء"""
        errors = []
        
        # التحقق من عدم تكرار الأسماء في الملف نفسه
        duplicates = df[df.duplicated(subset=['name'], keep=False)]
        if not duplicates.empty:
            duplicate_names = duplicates['name'].unique()
            errors.append(f"أسماء مكررة في الملف: {', '.join(duplicate_names[:5])}")
        
        return errors


# إنشاء نسخة من المعالج
customer_handler = CustomerImportExport()


@bp.route('/import/preview', methods=['POST'])
def preview_import():
    """معاينة الاستيراد قبل التنفيذ"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
    
    try:
        # قراءة الملف
        file_content = file.read()
        df, errors, metadata = customer_handler.import_file(file_content, file.filename)
        
        if errors and df.empty:
            return jsonify({
                'success': False,
                'message': 'فشل في قراءة الملف',
                'errors': errors[:10],
                'total_errors': len(errors)
            }), 400
        
        # التحقق من البيانات المكررة في قاعدة البيانات
        warnings = []
        if not df.empty:
            existing_names = set()
            for name in df['name'].unique():
                if Customer.query.filter_by(name=name).first():
                    existing_names.add(name)
            
            if existing_names:
                warnings.append(f"عملاء موجودون بالفعل: {', '.join(list(existing_names)[:5])}{'...' if len(existing_names) > 5 else ''}")
        
        # التحقق الإضافي
        validation_errors = customer_handler.validate_customer_data(df)
        errors.extend(validation_errors)
        
        # إعداد معاينة البيانات (أول 10 صفوف)
        preview_data = []
        if not df.empty:
            preview_df = df.head(10)
            for _, row in preview_df.iterrows():
                preview_data.append({
                    'الاسم': row.get('name', ''),
                    'الهاتف': row.get('phone', ''),
                    'البريد': row.get('email', ''),
                    'الرقم القومي': row.get('national_id', ''),
                    'العنوان': row.get('address', ''),
                    'الحالة': row.get('status', 'نشط')
                })
        
        return jsonify({
            'success': True,
            'total_rows': metadata.get('total_rows', 0),
            'valid_rows': len(df),
            'error_count': len(errors),
            'errors': errors[:10],
            'warnings': warnings,
            'preview': preview_data,
            'encoding': metadata.get('encoding'),
            'has_more_errors': len(errors) > 10
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في معالجة الملف: {str(e)}'
        }), 500


@bp.route('/import', methods=['POST'])
def import_customers():
    """تنفيذ الاستيراد الفعلي"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'لم يتم اختيار ملف'}), 400
    
    # التحقق من التأكيد
    if request.form.get('confirm') != 'true':
        return jsonify({'success': False, 'message': 'يجب تأكيد الاستيراد'}), 400
    
    result = ImportResult()
    
    try:
        # قراءة الملف
        file_content = file.read()
        df, errors, metadata = customer_handler.import_file(file_content, file.filename)
        
        result.metadata = metadata
        result.errors.extend(errors)
        
        if errors and df.empty:
            result.success = False
            result.error_count = len(errors)
            return jsonify(result.to_dict()), 400
        
        # معالجة كل صف
        for idx, row in df.iterrows():
            try:
                name = row.get('name', '').strip()
                if not name:
                    result.errors.append(f"السطر {idx + 2}: الاسم مطلوب")
                    result.error_count += 1
                    continue
                
                # التحقق من وجود العميل
                existing = Customer.query.filter_by(name=name).first()
                if existing:
                    result.skipped_count += 1
                    result.skipped_items.append(name)
                    continue
                
                # إنشاء عميل جديد
                customer = Customer(
                    id=generate_uid('C'),
                    code=generate_customer_code(),
                    name=name,
                    phone=row.get('phone') or None,
                    email=row.get('email') or None,
                    national_id=row.get('national_id') or None,
                    address=row.get('address') or None,
                    status=row.get('status', 'نشط'),
                    notes=row.get('notes') or None
                )
                
                db.session.add(customer)
                result.imported_count += 1
                
            except Exception as e:
                result.errors.append(f"السطر {idx + 2}: {str(e)}")
                result.error_count += 1
        
        # حفظ التغييرات
        if result.imported_count > 0:
            db.session.commit()
            log_action('استيراد عملاء', {
                'imported': result.imported_count,
                'skipped': result.skipped_count,
                'errors': result.error_count
            })
            result.success = True
        else:
            result.success = False
            if not result.errors:
                result.errors.append('لم يتم استيراد أي سجلات')
        
        return jsonify(result.to_dict())
        
    except Exception as e:
        db.session.rollback()
        result.success = False
        result.errors.append(f'خطأ في معالجة الملف: {str(e)}')
        return jsonify(result.to_dict()), 500


@bp.route('/export/<format>')
def export_customers(format):
    """تصدير العملاء بالتنسيق المطلوب"""
    try:
        # بناء الاستعلام
        query = Customer.query
        
        # تطبيق الفلاتر
        status_filter = request.args.get('status')
        if status_filter == 'active':
            query = query.filter_by(status='نشط')
        
        # جلب البيانات
        customers = query.order_by(Customer.name).all()
        
        # تحضير البيانات للتصدير
        data = customer_handler.prepare_export_data(customers)
        
        # التصدير حسب التنسيق
        if format == 'csv':
            return customer_handler.export_csv(data, 'customers')
        elif format == 'excel':
            return customer_handler.export_excel(data, 'customers')
        elif format == 'json':
            return customer_handler.export_json(data, 'customers')
        else:
            return jsonify({'success': False, 'message': 'تنسيق غير مدعوم'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'خطأ في التصدير: {str(e)}'}), 500