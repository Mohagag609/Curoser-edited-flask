from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from acc.blueprints.suppliers import bp
from acc.extensions import db
from acc.models import Supplier
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from acc.services.code_generator import generate_supplier_code
from sqlalchemy import or_, func
import json
import csv
import io
from datetime import datetime


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    
    suppliers = Supplier.query
    
    if q:
        suppliers = suppliers.filter(
            or_(
                Supplier.name.contains(q),
                Supplier.phone.contains(q),
                Supplier.email.contains(q),
                Supplier.address.contains(q)
            )
        )
    
    suppliers = suppliers.order_by(Supplier.name)
    pagination = Pagination(suppliers, page)
    
    return render_template('suppliers/index.html', 
                         suppliers=pagination.items, 
                         pagination=pagination,
                         q=q)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            address = request.form.get('address', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validate required fields
            if not name:
                flash('⚠️ الرجاء إدخال اسم المورد', 'warning')
                return redirect(url_for('suppliers.add'))
            
            # Check if supplier exists
            existing = Supplier.query.filter_by(name=name).first()
            if existing:
                flash('⚠️ يوجد مورد بنفس الاسم', 'warning')
                return redirect(url_for('suppliers.add'))
            
            # Create supplier with auto-generated code
            supplier = Supplier(
                id=generate_uid('S'),
                code=generate_supplier_code(),
                name=name,
                phone=phone,
                email=email,
                address=address,
                notes=notes
            )
            
            db.session.add(supplier)
            db.session.commit()
            
            # Log action
            log_action('إضافة مورد', {'id': supplier.id, 'name': supplier.name})
            
            flash(f'✅ تم إضافة المورد "{supplier.name}" بنجاح', 'success')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'تم إضافة المورد "{supplier.name}" بنجاح',
                    'redirect': url_for('suppliers.index')
                })
            
            return redirect(url_for('suppliers.index'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'❌ خطأ في إضافة المورد: {str(e)}'
            flash(error_msg, 'error')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg}), 500
                
            return redirect(url_for('suppliers.add'))
    
    return render_template('suppliers/add.html')


@bp.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    supplier = Supplier.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            address = request.form.get('address', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validate
            if not name:
                flash('⚠️ الرجاء إدخال اسم المورد', 'warning')
                return redirect(url_for('suppliers.edit', id=id))
            
            # Check duplicate name
            existing = Supplier.query.filter_by(name=name).filter(Supplier.id != id).first()
            if existing:
                flash('⚠️ يوجد مورد آخر بنفس الاسم', 'warning')
                return redirect(url_for('suppliers.edit', id=id))
            
            # Update supplier
            supplier.name = name
            supplier.phone = phone
            supplier.email = email
            supplier.address = address
            supplier.notes = notes
            
            db.session.commit()
            
            # Log action
            log_action('تعديل مورد', {'id': supplier.id, 'name': supplier.name})
            
            flash(f'✅ تم تحديث المورد "{supplier.name}" بنجاح', 'success')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'تم تحديث المورد "{supplier.name}" بنجاح',
                    'redirect': url_for('suppliers.detail', id=id)
                })
            
            return redirect(url_for('suppliers.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'❌ خطأ في تحديث المورد: {str(e)}'
            flash(error_msg, 'error')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg}), 500
                
            return redirect(url_for('suppliers.edit', id=id))
    
    return render_template('suppliers/edit.html', supplier=supplier)


@bp.route('/detail/<id>')
def detail(id):
    supplier = Supplier.query.get_or_404(id)
    
    # Get related data
    materials_count = supplier.project_materials.count()
    total_amount = db.session.query(func.sum(supplier.project_materials.subquery().c.total_amount)).scalar() or 0
    
    return render_template('suppliers/detail.html', 
                         supplier=supplier,
                         materials_count=materials_count,
                         total_amount=total_amount,
                         format_currency=format_currency)


@bp.route('/delete/<id>', methods=['POST'])
def delete(id):
    try:
        supplier = Supplier.query.get_or_404(id)
        
        # Check if has materials
        if supplier.project_materials.count() > 0:
            flash('⚠️ لا يمكن حذف هذا المورد لوجود مواد مرتبطة به', 'warning')
            return redirect(url_for('suppliers.index'))
        
        # Store info before deletion
        supplier_name = supplier.name
        supplier_id = supplier.id
        
        # Delete supplier
        db.session.delete(supplier)
        db.session.commit()
        
        # Log action
        log_action('حذف مورد', {'id': supplier_id, 'name': supplier_name})
        
        flash(f'✅ تم حذف المورد "{supplier_name}" بنجاح', 'success')
        return redirect(url_for('suppliers.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ خطأ في حذف المورد: {str(e)}', 'error')
        return redirect(url_for('suppliers.index'))


@bp.route('/export/<format>')
def export(format):
    suppliers = Supplier.query.order_by(Supplier.name).all()
    
    if format == 'excel':
        # Generate HTML table for Excel
        html = generate_excel_html(suppliers)
        
        response = make_response(html)
        response.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=suppliers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
        
        return response
        
    elif format == 'json':
        data = [{
            'id': s.id,
            'code': s.code,
            'name': s.name,
            'phone': s.phone,
            'email': s.email,
            'address': s.address,
            'notes': s.notes,
            'created_at': s.created_at.isoformat() if s.created_at else None
        } for s in suppliers]
        
        response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=suppliers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return response
        
    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['الكود', 'الاسم', 'الهاتف', 'البريد الإلكتروني', 'العنوان', 'ملاحظات', 'تاريخ التسجيل'])
        
        # Data
        for s in suppliers:
            writer.writerow([
                s.code,
                s.name,
                s.phone or '',
                s.email or '',
                s.address or '',
                s.notes or '',
                s.created_at.strftime('%Y-%m-%d') if s.created_at else ''
            ])
        
        response = make_response('\ufeff' + output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = f'attachment; filename=suppliers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    else:
        flash('صيغة التصدير غير مدعومة', 'error')
        return redirect(url_for('suppliers.index'))


@bp.route('/import', methods=['GET', 'POST'])
def import_data():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file:
                flash('⚠️ الرجاء اختيار ملف', 'warning')
                return redirect(url_for('suppliers.import_data'))
            
            # Read file content
            content = file.read()
            filename = file.filename.lower()
            
            imported = 0
            skipped = 0
            errors = []
            
            if filename.endswith('.json'):
                # Import JSON
                try:
                    data = json.loads(content.decode('utf-8'))
                    for item in data:
                        if not item.get('name'):
                            skipped += 1
                            continue
                        
                        # Check if exists
                        if Supplier.query.filter_by(name=item['name']).first():
                            skipped += 1
                            continue
                        
                        supplier = Supplier(
                            id=generate_uid('S'),
                            code=generate_supplier_code(),
                            name=item['name'],
                            phone=item.get('phone', ''),
                            email=item.get('email', ''),
                            address=item.get('address', ''),
                            notes=item.get('notes', '')
                        )
                        db.session.add(supplier)
                        imported += 1
                        
                except Exception as e:
                    errors.append(f'خطأ في معالجة JSON: {str(e)}')
                    
            elif filename.endswith('.csv'):
                # Import CSV
                try:
                    # Try different encodings
                    for encoding in ['utf-8-sig', 'utf-8', 'windows-1256', 'iso-8859-1']:
                        try:
                            text = content.decode(encoding)
                            break
                        except:
                            continue
                    else:
                        raise ValueError('لا يمكن قراءة ترميز الملف')
                    
                    reader = csv.DictReader(io.StringIO(text))
                    for row in reader:
                        name = row.get('الاسم') or row.get('name') or row.get('Name')
                        if not name:
                            skipped += 1
                            continue
                        
                        # Check if exists
                        if Supplier.query.filter_by(name=name).first():
                            skipped += 1
                            continue
                        
                        supplier = Supplier(
                            id=generate_uid('S'),
                            code=generate_supplier_code(),
                            name=name,
                            phone=row.get('الهاتف') or row.get('phone') or row.get('Phone') or '',
                            email=row.get('البريد الإلكتروني') or row.get('email') or row.get('Email') or '',
                            address=row.get('العنوان') or row.get('address') or row.get('Address') or '',
                            notes=row.get('ملاحظات') or row.get('notes') or row.get('Notes') or ''
                        )
                        db.session.add(supplier)
                        imported += 1
                        
                except Exception as e:
                    errors.append(f'خطأ في معالجة CSV: {str(e)}')
            
            else:
                flash('⚠️ نوع الملف غير مدعوم. يرجى استخدام JSON أو CSV', 'warning')
                return redirect(url_for('suppliers.import_data'))
            
            if imported > 0:
                db.session.commit()
                log_action('استيراد موردين', {'count': imported})
            
            # Show results
            if imported > 0:
                flash(f'✅ تم استيراد {imported} مورد بنجاح', 'success')
            if skipped > 0:
                flash(f'ℹ️ تم تخطي {skipped} مورد (موجود مسبقاً)', 'info')
            if errors:
                for error in errors:
                    flash(f'❌ {error}', 'error')
            
            return redirect(url_for('suppliers.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ خطأ في الاستيراد: {str(e)}', 'error')
            return redirect(url_for('suppliers.import_data'))
    
    return render_template('suppliers/import.html')


@bp.route('/report')
def report():
    # Get statistics
    total_suppliers = Supplier.query.count()
    active_suppliers = Supplier.query.join(Supplier.project_materials).distinct().count()
    
    # Top suppliers by amount
    top_suppliers = db.session.query(
        Supplier,
        func.count(Supplier.project_materials).label('materials_count'),
        func.sum(Supplier.project_materials.subquery().c.total_amount).label('total_amount')
    ).join(Supplier.project_materials).group_by(Supplier.id).order_by(
        func.sum(Supplier.project_materials.subquery().c.total_amount).desc()
    ).limit(10).all()
    
    return render_template('suppliers/report.html',
                         total_suppliers=total_suppliers,
                         active_suppliers=active_suppliers,
                         top_suppliers=top_suppliers,
                         format_currency=format_currency)


def generate_excel_html(suppliers):
    """Generate HTML table for Excel export"""
    html = '''
    <html xmlns:o="urn:schemas-microsoft-com:office:office"
          xmlns:x="urn:schemas-microsoft-com:office:excel"
          xmlns="http://www.w3.org/TR/REC-html40">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <style>
            table {
                border-collapse: collapse;
                width: 100%;
            }
            th {
                background-color: #366092;
                color: white;
                font-weight: bold;
                padding: 10px;
                text-align: right;
                border: 1px solid #ddd;
            }
            td {
                padding: 8px;
                text-align: right;
                border: 1px solid #ddd;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h1>قائمة الموردين</h1>
        <table>
            <thead>
                <tr>
                    <th>الكود</th>
                    <th>الاسم</th>
                    <th>الهاتف</th>
                    <th>البريد الإلكتروني</th>
                    <th>العنوان</th>
                    <th>ملاحظات</th>
                    <th>تاريخ التسجيل</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for supplier in suppliers:
        html += f'''
            <tr>
                <td>{supplier.code}</td>
                <td>{supplier.name}</td>
                <td>{supplier.phone or ''}</td>
                <td>{supplier.email or ''}</td>
                <td>{supplier.address or ''}</td>
                <td>{supplier.notes or ''}</td>
                <td>{supplier.created_at.strftime('%Y-%m-%d') if supplier.created_at else ''}</td>
            </tr>
        '''
    
    html += '''
            </tbody>
        </table>
    </body>
    </html>
    '''
    
    return html