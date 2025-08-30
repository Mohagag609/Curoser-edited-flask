from flask import render_template, request, redirect, url_for, flash, jsonify, Response, send_file
from acc.blueprints.materials import bp
from acc.models import Material, ProjectMaterial, Project
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from acc.services.code_generator import generate_material_code
from acc.services.import_handler import ImportHandler
from sqlalchemy import func, or_
import io
import csv
import json
from datetime import datetime

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    category = request.args.get('category', '')
    
    # Base query
    query = Material.query
    
    # Search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Material.name.ilike(search_term),
                Material.code.ilike(search_term),
                Material.unit.ilike(search_term),
                Material.category.ilike(search_term),
                Material.description.ilike(search_term)
            )
        )
    
    # Filter by category
    if category:
        query = query.filter(Material.category == category)
    
    # Order by created date desc
    query = query.order_by(Material.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    materials = pagination.items
    
    # Get unique categories for filter
    categories = db.session.query(Material.category).distinct().filter(Material.category.isnot(None)).all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('materials/index.html',
                         materials=materials,
                         pagination=pagination,
                         q=q,
                         category=category,
                         categories=categories)


@bp.route('/search')
def search():
    """Advanced search endpoint for AJAX"""
    q = request.args.get('q', '')
    category = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    
    query = Material.query
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Material.name.ilike(search_term),
                Material.code.ilike(search_term),
                Material.unit.ilike(search_term),
                Material.category.ilike(search_term),
                Material.description.ilike(search_term)
            )
        )
    
    # Category filter
    if category:
        query = query.filter(Material.category == category)
    
    # Order by
    query = query.order_by(Material.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Get unique categories
    categories = db.session.query(Material.category).distinct().filter(Material.category.isnot(None)).all()
    categories = [c[0] for c in categories if c[0]]
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('materials/_results.html',
                             materials=pagination.items,
                             pagination=pagination,
                             q=q,
                             category=category,
                             categories=categories)
    
    return render_template('materials/index.html',
                         materials=pagination.items,
                         pagination=pagination,
                         q=q,
                         category=category,
                         categories=categories)


@bp.route('/<id>')
def detail(id):
    material = Material.query.get_or_404(id)
    
    # Get material usage in projects
    project_materials = ProjectMaterial.query.filter_by(material_id=id).order_by(ProjectMaterial.created_at.desc()).all()
    
    # Calculate statistics
    total_used = db.session.query(func.sum(ProjectMaterial.quantity)).filter_by(material_id=id).scalar() or 0
    total_value = db.session.query(func.sum(ProjectMaterial.total_price)).filter_by(material_id=id).scalar() or 0
    
    return render_template('materials/detail.html',
                         material=material,
                         project_materials=project_materials,
                         total_used=total_used,
                         total_value=total_value)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        unit = request.form.get('unit', '').strip()
        unit_cost = request.form.get('unit_cost', 0)
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        min_stock = request.form.get('min_stock', 0)
        
        # Validation
        if not name:
            error_msg = 'اسم المادة مطلوب'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.add'))
        
        if not unit:
            error_msg = 'وحدة القياس مطلوبة'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.add'))
        
        try:
            material = Material(
                id=generate_uid('MAT'),
                code=generate_material_code(),
                name=name,
                unit=unit,
                unit_cost=float(unit_cost) if unit_cost else 0,
                category=category,
                description=description,
                min_stock=float(min_stock) if min_stock else 0,
                current_stock=0
            )
            
            db.session.add(material)
            log_action('إضافة مادة جديدة', {'id': material.id, 'name': material.name})
            db.session.commit()
            
            success_msg = f'تم إضافة المادة بنجاح! رقم المادة: {material.code}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('materials.detail', id=material.id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('materials.detail', id=material.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء إضافة المادة: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.add'))
    
    return render_template('materials/add.html')


@bp.route('/<id>/edit', methods=['GET', 'POST'])
def edit(id):
    material = Material.query.get_or_404(id)
    
    if request.method == 'POST':
        material.name = request.form.get('name', '').strip()
        material.unit = request.form.get('unit', '').strip()
        material.unit_cost = float(request.form.get('unit_cost', 0))
        material.category = request.form.get('category', '').strip()
        material.description = request.form.get('description', '').strip()
        material.min_stock = float(request.form.get('min_stock', 0))
        
        if not material.name:
            error_msg = 'اسم المادة مطلوب'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.edit', id=id))
        
        if not material.unit:
            error_msg = 'وحدة القياس مطلوبة'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.edit', id=id))
        
        try:
            log_action('تعديل مادة', {'id': material.id, 'name': material.name})
            db.session.commit()
            
            success_msg = 'تم تعديل المادة بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('materials.detail', id=id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('materials.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء تعديل المادة: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.edit', id=id))
    
    return render_template('materials/edit.html', material=material)


@bp.route('/<id>/delete', methods=['POST'])
def delete(id):
    try:
        material = Material.query.get_or_404(id)
        
        # Check if material is used in projects
        if material.project_uses.count() > 0:
            error_msg = f'لا يمكن حذف المادة "{material.name}" لأنها مستخدمة في مشاريع'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('materials.detail', id=id))
        
        material_name = material.name
        material_id = material.id
        
        db.session.delete(material)
        db.session.commit()
        
        log_action('حذف مادة', {'id': material_id, 'name': material_name})
        
        success_msg = f'تم حذف المادة "{material_name}" بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'✅ {success_msg}'
            })
        
        flash(f'✅ {success_msg}', 'success')
        return redirect(url_for('materials.index'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'خطأ في حذف المادة: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
        
        flash(f'❌ {error_msg}', 'error')
        return redirect(url_for('materials.index'))


@bp.route('/export/<format>')
def export(format):
    """تصدير بيانات المواد"""
    materials = Material.query.order_by(Material.name).all()
    
    if format == 'excel':
        # Generate Excel file (HTML table format)
        output = io.StringIO()
        output.write('<html><head><meta charset="utf-8"></head><body>')
        output.write('<table border="1">')
        output.write('<tr>')
        output.write('<th>الكود</th>')
        output.write('<th>الاسم</th>')
        output.write('<th>الوحدة</th>')
        output.write('<th>السعر الافتراضي</th>')
        output.write('<th>الفئة</th>')
        output.write('<th>الحد الأدنى للمخزون</th>')
        output.write('<th>المخزون الحالي</th>')
        output.write('<th>الوصف</th>')
        output.write('</tr>')
        
        for material in materials:
            output.write('<tr>')
            output.write(f'<td>{material.code}</td>')
            output.write(f'<td>{material.name}</td>')
            output.write(f'<td>{material.unit or "-"}</td>')
            output.write(f'<td>{format_currency(material.unit_cost)}</td>')
            output.write(f'<td>{material.category or "-"}</td>')
            output.write(f'<td>{material.min_stock or 0}</td>')
            output.write(f'<td>{material.current_stock or 0}</td>')
            output.write(f'<td>{material.description or "-"}</td>')
            output.write('</tr>')
        
        output.write('</table></body></html>')
        
        response = Response(output.getvalue(), mimetype='application/vnd.ms-excel')
        response.headers['Content-Disposition'] = f'attachment; filename=materials_{datetime.now().strftime("%Y%m%d")}.xls'
        return response
    
    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['الكود', 'الاسم', 'الوحدة', 'السعر الافتراضي', 'الفئة', 'الحد الأدنى للمخزون', 'المخزون الحالي', 'الوصف'])
        
        # Write data
        for material in materials:
            writer.writerow([
                material.code,
                material.name,
                material.unit or '-',
                material.unit_cost or 0,
                material.category or '-',
                material.min_stock or 0,
                material.current_stock or 0,
                material.description or '-'
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'materials_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    
    elif format == 'json':
        data = []
        for material in materials:
            data.append({
                'code': material.code,
                'name': material.name,
                'unit': material.unit,
                'unit_cost': float(material.unit_cost) if material.unit_cost else 0,
                'category': material.category,
                'min_stock': float(material.min_stock) if material.min_stock else 0,
                'current_stock': float(material.current_stock) if material.current_stock else 0,
                'description': material.description
            })
        
        return jsonify({
            'export_date': datetime.now().isoformat(),
            'total_count': len(data),
            'materials': data
        })
    
    else:
        flash('صيغة التصدير غير مدعومة', 'error')
        return redirect(url_for('materials.index'))


@bp.route('/import', methods=['GET', 'POST'])
def import_data():
    """استيراد بيانات المواد"""
    if request.method == 'GET':
        return render_template('materials/import.html')
    
    if 'file' not in request.files:
        flash('❌ الرجاء اختيار ملف', 'error')
        return redirect(url_for('materials.import_data'))
    
    file = request.files['file']
    if file.filename == '':
        flash('❌ الرجاء اختيار ملف', 'error')
        return redirect(url_for('materials.import_data'))
    
    try:
        # قراءة محتوى الملف
        file_content = file.read()
        
        # استخدام ImportHandler
        data, import_errors, file_type = ImportHandler.import_file(file_content, file.filename)
        
        if import_errors and not data:
            for error in import_errors[:5]:
                flash(f'❌ {error}', 'error')
            if len(import_errors) > 5:
                flash(f'... و {len(import_errors) - 5} أخطاء أخرى', 'error')
            return redirect(url_for('materials.import_data'))
        
        imported_count = 0
        skipped_count = 0
        failed_count = 0
        errors = []
        skipped_names = []
        
        # معالجة البيانات المستوردة
        for index, item in enumerate(data):
            try:
                name = item.get('name', '').strip()
                if not name:
                    failed_count += 1
                    errors.append(f"السطر {index + 2}: الاسم مطلوب")
                    continue
                
                # التحقق من وجود المادة
                existing = Material.query.filter_by(name=name).first()
                if existing:
                    skipped_count += 1
                    skipped_names.append(name)
                    continue
                
                # إنشاء مادة جديدة
                material = Material(
                    id=generate_uid('MAT'),
                    code=generate_material_code(),
                    name=name,
                    unit=item.get('unit', '').strip() or 'قطعة',
                    unit_cost=float(item.get('unit_cost', 0)) if item.get('unit_cost') else 0,
                    category=item.get('category', '').strip() or None,
                    description=item.get('description', '').strip() or None,
                    min_stock=float(item.get('min_stock', 0)) if item.get('min_stock') else 0,
                    current_stock=float(item.get('current_stock', 0)) if item.get('current_stock') else 0
                )
                
                db.session.add(material)
                imported_count += 1
                
            except Exception as e:
                failed_count += 1
                errors.append(f"السطر {index + 2}: {str(e)}")
        
        # حفظ التغييرات
        if imported_count > 0:
            log_action('استيراد مواد', {'imported': imported_count, 'skipped': skipped_count})
            db.session.commit()
        
        # عرض النتائج
        return render_template('materials/import_result.html',
                             imported_count=imported_count,
                             skipped_count=skipped_count,
                             skipped_names=skipped_names,
                             failed_count=failed_count,
                             errors=errors)
        
    except Exception as e:
        flash(f'❌ خطأ في معالجة الملف: {str(e)}', 'error')
        return redirect(url_for('materials.import_data'))


@bp.route('/report')
def report():
    """عرض صفحة التقارير"""
    # إحصائيات عامة
    total_materials = Material.query.count()
    total_categories = db.session.query(func.count(func.distinct(Material.category))).scalar() or 0
    
    # المواد الأكثر استخداماً
    most_used = db.session.query(
        Material,
        func.sum(ProjectMaterial.quantity).label('total_quantity'),
        func.count(ProjectMaterial.id).label('usage_count')
    ).join(ProjectMaterial).group_by(Material.id).order_by(
        func.sum(ProjectMaterial.quantity).desc()
    ).limit(10).all()
    
    # المواد منخفضة المخزون
    low_stock = Material.query.filter(
        Material.current_stock < Material.min_stock
    ).order_by(Material.name).all()
    
    # إحصائيات حسب الفئة
    category_stats = db.session.query(
        Material.category,
        func.count(Material.id).label('count'),
        func.avg(Material.unit_cost).label('avg_cost')
    ).group_by(Material.category).all()
    
    return render_template('materials/report.html',
                         total_materials=total_materials,
                         total_categories=total_categories,
                         most_used=most_used,
                         low_stock=low_stock,
                         category_stats=category_stats)


@bp.route('/api/materials')
def api_materials():
    """API endpoint for materials autocomplete"""
    materials = Material.query.order_by(Material.name).all()
    return jsonify([{
        'id': m.id,
        'code': m.code,
        'name': m.name,
        'unit': m.unit,
        'unit_cost': float(m.unit_cost) if m.unit_cost else 0,
        'category': m.category
    } for m in materials])