"""
مسارات الاستيراد والتصدير
"""
from flask import Blueprint, request, jsonify, render_template, g
from acc.decorators import login_required
from werkzeug.utils import secure_filename
from .importer_lite import GenericImporter
from .exporter_lite import GenericExporter
from .schemas import list_resources, get_schema
import os

# حد أقصى لحجم الملف: 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024

# الامتدادات المسموحة
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

bp = Blueprint('io', __name__, url_prefix='/io')

def allowed_file(filename):
    """التحقق من امتداد الملف"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
@login_required
def index():
    """الصفحة الرئيسية للاستيراد/التصدير"""
    resources = list_resources()
    return render_template('io/index.html', resources=resources)

@bp.route('/<resource>')
@login_required
def resource_page(resource):
    """صفحة استيراد/تصدير مورد محدد"""
    schema = get_schema(resource)
    if not schema:
        return "مورد غير موجود", 404
    
    return render_template('io/resource.html', 
                         resource=resource,
                         schema=schema,
                         current_project=g.get('current_project', None))

@bp.route('/<resource>/import', methods=['POST'])
@login_required
def import_data(resource):
    """استيراد البيانات"""
    try:
        # التحقق من وجود ملف
        if 'file' not in request.files:
            return jsonify({
                'ok': False,
                'message': 'لم يتم اختيار ملف',
                'report': {'errors': [{'row': 0, 'error': 'لم يتم اختيار ملف'}]}
            }), 400
        
        file = request.files['file']
        
        # التحقق من اختيار ملف
        if file.filename == '':
            return jsonify({
                'ok': False,
                'message': 'لم يتم اختيار ملف',
                'report': {'errors': [{'row': 0, 'error': 'لم يتم اختيار ملف'}]}
            }), 400
        
        # التحقق من الامتداد
        if not allowed_file(file.filename):
            return jsonify({
                'ok': False,
                'message': 'صيغة الملف غير مدعومة. استخدم CSV أو Excel',
                'report': {'errors': [{'row': 0, 'error': 'صيغة ملف غير مدعومة'}]}
            }), 400
        
        # قراءة محتوى الملف
        file_content = file.read()
        
        # التحقق من الحجم
        if len(file_content) > MAX_FILE_SIZE:
            return jsonify({
                'ok': False,
                'message': 'حجم الملف كبير جداً (الحد الأقصى 5MB)',
                'report': {'errors': [{'row': 0, 'error': 'حجم الملف كبير جداً'}]}
            }), 400
        
        # الحصول على وضع الاستيراد
        mode = request.form.get('mode', 'insert')
        if mode not in ['insert', 'upsert']:
            mode = 'insert'
        
        # تنفيذ الاستيراد
        importer = GenericImporter(resource)
        result = importer.import_file(file_content, file.filename, mode)
        
        return jsonify(result.to_dict())
        
    except ValueError as e:
        return jsonify({
            'ok': False,
            'message': str(e),
            'report': {'errors': [{'row': 0, 'error': str(e)}]}
        }), 400
    except Exception as e:
        return jsonify({
            'ok': False,
            'message': 'حدث خطأ في النظام',
            'report': {'errors': [{'row': 0, 'error': str(e)}]}
        }), 500

@bp.route('/<resource>/export')
@login_required
def export_data(resource):
    """تصدير البيانات"""
    try:
        format = request.args.get('format', 'csv')
        
        exporter = GenericExporter(resource)
        
        if format == 'xlsx':
            return exporter.export_excel()
        else:
            return exporter.export_csv()
            
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        return f"خطأ في التصدير: {str(e)}", 500

@bp.route('/<resource>/template')
@login_required
def download_template(resource):
    """تحميل قالب للاستيراد"""
    try:
        format = request.args.get('format', 'csv')
        
        exporter = GenericExporter(resource)
        return exporter.generate_template(format)
        
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        return f"خطأ في توليد القالب: {str(e)}", 500