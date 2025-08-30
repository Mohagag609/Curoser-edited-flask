"""
مسارات الاستيراد والتصدير
"""
from flask import Blueprint, request, jsonify, render_template, g, current_app
from acc.decorators import login_required
from werkzeug.utils import secure_filename
from .importer_lite import GenericImporter
from .exporter_lite import GenericExporter
from .schemas import list_resources, get_schema
import os

# حد أقصى لحجم الملف: 1MB (مؤقتاً لتجنب timeout)
MAX_FILE_SIZE = 1 * 1024 * 1024

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
    # مؤقتاً - إرجاع JSON بسيط
    return jsonify({
        'message': 'نظام الاستيراد/التصدير',
        'resources': resources
    })

@bp.route('/<resource>')
@login_required  
def resource_page(resource):
    """صفحة استيراد/تصدير مورد محدد"""
    try:
        schema = get_schema(resource)
        if not schema:
            return jsonify({'error': f'مورد غير موجود: {resource}'}), 404
        
        # HTML مباشر مؤقتاً
        html = f'''
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>استيراد/تصدير {schema.plural_name}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-gray-100">
    <div class="container mx-auto p-6">
        <div class="bg-white rounded-lg shadow p-6">
            <h1 class="text-2xl font-bold mb-4">استيراد وتصدير {schema.plural_name}</h1>
            
            <form method="POST" action="/io/{resource}/import" enctype="multipart/form-data" class="mb-6">
                <div class="mb-4">
                    <label class="block text-gray-700 text-sm font-bold mb-2">
                        اختر ملف CSV:
                    </label>
                    <input type="file" name="file" accept=".csv" required 
                           class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700">
                </div>
                
                <div class="mb-4">
                    <label class="block text-gray-700 text-sm font-bold mb-2">
                        وضع الاستيراد:
                    </label>
                    <select name="mode" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700">
                        <option value="insert">إدراج فقط (تخطي المكررات)</option>
                        <option value="upsert">إدراج أو تحديث</option>
                    </select>
                </div>
                
                <button type="submit" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                    بدء الاستيراد
                </button>
            </form>
            
            <hr class="my-6">
            
            <div class="flex gap-4">
                <a href="/io/{resource}/export?format=csv" 
                   class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">
                    تصدير CSV
                </a>
                
                <a href="/io/{resource}/template?format=csv" 
                   class="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded">
                    تحميل قالب
                </a>
                
                <a href="/customers" 
                   class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded">
                    رجوع
                </a>
            </div>
            
            <div class="mt-6 bg-gray-100 p-4 rounded">
                <h3 class="font-bold mb-2">الأعمدة المطلوبة:</h3>
                <ul class="list-disc list-inside">
                    {"".join([f'<li>{col["label"]} {"(مطلوب)" if col.get("required") else "(اختياري)"}</li>' for col in schema.columns])}
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
        '''
        
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
        
    except Exception as e:
        current_app.logger.error(f"Error loading resource page for {resource}: {str(e)}", exc_info=True)
        return jsonify({'error': f'خطأ في تحميل الصفحة: {str(e)}'}), 500

@bp.route('/<resource>/import', methods=['POST'])
@login_required
def import_data(resource):
    """استيراد البيانات"""
    current_app.logger.info(f"Starting import for resource: {resource}")
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
                'message': 'حجم الملف كبير جداً (الحد الأقصى 1MB)',
                'report': {'errors': [{'row': 0, 'error': 'حجم الملف كبير جداً'}]}
            }), 400
        
        # الحصول على وضع الاستيراد
        mode = request.form.get('mode', 'insert')
        if mode not in ['insert', 'upsert']:
            mode = 'insert'
        
        # تنفيذ الاستيراد
        current_app.logger.info(f"Creating importer for {resource}")
        importer = GenericImporter(resource)
        
        current_app.logger.info(f"Starting import_file for {file.filename}")
        result = importer.import_file(file_content, file.filename, mode)
        
        current_app.logger.info(f"Import completed: {result.get_message()}")
        return jsonify(result.to_dict())
        
    except ValueError as e:
        return jsonify({
            'ok': False,
            'message': str(e),
            'report': {'errors': [{'row': 0, 'error': str(e)}]}
        }), 400
    except Exception as e:
        current_app.logger.error(f"Import error for {resource}: {str(e)}", exc_info=True)
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