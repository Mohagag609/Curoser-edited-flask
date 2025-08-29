from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from acc.blueprints.contractors import bp
from acc.extensions import db
from acc.models import Contractor
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from acc.services.code_generator import generate_contractor_code
from sqlalchemy import or_, func
import json
import csv
import io
from datetime import datetime


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    
    contractors = Contractor.query
    
    if q:
        contractors = contractors.filter(
            or_(
                Contractor.name.contains(q),
                Contractor.phone.contains(q),
                Contractor.email.contains(q),
                Contractor.specialty.contains(q),
                Contractor.address.contains(q)
            )
        )
    
    contractors = contractors.order_by(Contractor.name)
    pagination = Pagination(contractors, page)
    
    return render_template('contractors/index.html', 
                         contractors=pagination.items, 
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
            specialty = request.form.get('specialty', '').strip()
            address = request.form.get('address', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validate required fields
            if not name:
                flash('⚠️ الرجاء إدخال اسم المقاول', 'warning')
                return redirect(url_for('contractors.add'))
            
            # Check if contractor exists
            existing = Contractor.query.filter_by(name=name).first()
            if existing:
                flash('⚠️ يوجد مقاول بنفس الاسم', 'warning')
                return redirect(url_for('contractors.add'))
            
            # Create contractor with auto-generated code
            contractor = Contractor(
                id=generate_uid('CON'),
                code=generate_contractor_code(),
                name=name,
                phone=phone,
                email=email,
                specialty=specialty,
                address=address,
                notes=notes
            )
            
            db.session.add(contractor)
            db.session.commit()
            
            # Log action
            log_action('إضافة مقاول', {'id': contractor.id, 'name': contractor.name})
            
            flash(f'✅ تم إضافة المقاول "{contractor.name}" بنجاح', 'success')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'تم إضافة المقاول "{contractor.name}" بنجاح',
                    'redirect': url_for('contractors.index')
                })
            
            return redirect(url_for('contractors.index'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'❌ خطأ في إضافة المقاول: {str(e)}'
            flash(error_msg, 'error')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg}), 500
                
            return redirect(url_for('contractors.add'))
    
    return render_template('contractors/add.html')


@bp.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    contractor = Contractor.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()
            specialty = request.form.get('specialty', '').strip()
            address = request.form.get('address', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validate
            if not name:
                flash('⚠️ الرجاء إدخال اسم المقاول', 'warning')
                return redirect(url_for('contractors.edit', id=id))
            
            # Check duplicate name
            existing = Contractor.query.filter_by(name=name).filter(Contractor.id != id).first()
            if existing:
                flash('⚠️ يوجد مقاول آخر بنفس الاسم', 'warning')
                return redirect(url_for('contractors.edit', id=id))
            
            # Update contractor
            contractor.name = name
            contractor.phone = phone
            contractor.email = email
            contractor.specialty = specialty
            contractor.address = address
            contractor.notes = notes
            
            db.session.commit()
            
            # Log action
            log_action('تعديل مقاول', {'id': contractor.id, 'name': contractor.name})
            
            flash(f'✅ تم تحديث المقاول "{contractor.name}" بنجاح', 'success')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'تم تحديث المقاول "{contractor.name}" بنجاح',
                    'redirect': url_for('contractors.detail', id=id)
                })
            
            return redirect(url_for('contractors.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'❌ خطأ في تحديث المقاول: {str(e)}'
            flash(error_msg, 'error')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg}), 500
                
            return redirect(url_for('contractors.edit', id=id))
    
    return render_template('contractors/edit.html', contractor=contractor)


@bp.route('/detail/<id>')
def detail(id):
    contractor = Contractor.query.get_or_404(id)
    
    # Get related data
    # TODO: Add project stages when model is available
    projects_count = 0  # Placeholder
    total_value = 0  # Placeholder
    
    return render_template('contractors/detail.html', 
                         contractor=contractor,
                         projects_count=projects_count,
                         total_value=total_value,
                         format_currency=format_currency)


@bp.route('/delete/<id>', methods=['POST'])
def delete(id):
    try:
        contractor = Contractor.query.get_or_404(id)
        
        # Check if has projects
        # TODO: Check project stages when available
        
        # Store info before deletion
        contractor_name = contractor.name
        contractor_id = contractor.id
        
        # Delete contractor
        db.session.delete(contractor)
        db.session.commit()
        
        # Log action
        log_action('حذف مقاول', {'id': contractor_id, 'name': contractor_name})
        
        flash(f'✅ تم حذف المقاول "{contractor_name}" بنجاح', 'success')
        return redirect(url_for('contractors.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ خطأ في حذف المقاول: {str(e)}', 'error')
        return redirect(url_for('contractors.index'))


@bp.route('/export/<format>')
def export(format):
    contractors = Contractor.query.order_by(Contractor.name).all()
    
    if format == 'excel':
        # Generate HTML table for Excel
        html = generate_excel_html(contractors)
        
        response = make_response(html)
        response.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=contractors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
        
        return response
        
    elif format == 'json':
        data = [{
            'id': c.id,
            'code': c.code,
            'name': c.name,
            'phone': c.phone,
            'email': c.email,
            'specialty': c.specialty,
            'address': c.address,
            'notes': c.notes,
            'created_at': c.created_at.isoformat() if c.created_at else None
        } for c in contractors]
        
        response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=contractors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return response
        
    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['الكود', 'الاسم', 'الهاتف', 'البريد الإلكتروني', 'التخصص', 'العنوان', 'ملاحظات', 'تاريخ التسجيل'])
        
        # Data
        for c in contractors:
            writer.writerow([
                c.code,
                c.name,
                c.phone or '',
                c.email or '',
                c.specialty or '',
                c.address or '',
                c.notes or '',
                c.created_at.strftime('%Y-%m-%d') if c.created_at else ''
            ])
        
        response = make_response('\ufeff' + output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = f'attachment; filename=contractors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    else:
        flash('صيغة التصدير غير مدعومة', 'error')
        return redirect(url_for('contractors.index'))


@bp.route('/import', methods=['GET', 'POST'])
def import_data():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file:
                flash('⚠️ الرجاء اختيار ملف', 'warning')
                return redirect(url_for('contractors.import_data'))
            
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
                        if Contractor.query.filter_by(name=item['name']).first():
                            skipped += 1
                            continue
                        
                        contractor = Contractor(
                            id=generate_uid('CON'),
                            code=generate_contractor_code(),
                            name=item['name'],
                            phone=item.get('phone', ''),
                            email=item.get('email', ''),
                            specialty=item.get('specialty', ''),
                            address=item.get('address', ''),
                            notes=item.get('notes', '')
                        )
                        db.session.add(contractor)
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
                        if Contractor.query.filter_by(name=name).first():
                            skipped += 1
                            continue
                        
                        contractor = Contractor(
                            id=generate_uid('CON'),
                            code=generate_contractor_code(),
                            name=name,
                            phone=row.get('الهاتف') or row.get('phone') or row.get('Phone') or '',
                            email=row.get('البريد الإلكتروني') or row.get('email') or row.get('Email') or '',
                            specialty=row.get('التخصص') or row.get('specialty') or row.get('Specialty') or '',
                            address=row.get('العنوان') or row.get('address') or row.get('Address') or '',
                            notes=row.get('ملاحظات') or row.get('notes') or row.get('Notes') or ''
                        )
                        db.session.add(contractor)
                        imported += 1
                        
                except Exception as e:
                    errors.append(f'خطأ في معالجة CSV: {str(e)}')
            
            else:
                flash('⚠️ نوع الملف غير مدعوم. يرجى استخدام JSON أو CSV', 'warning')
                return redirect(url_for('contractors.import_data'))
            
            if imported > 0:
                db.session.commit()
                log_action('استيراد مقاولين', {'count': imported})
            
            # Show results
            if imported > 0:
                flash(f'✅ تم استيراد {imported} مقاول بنجاح', 'success')
            if skipped > 0:
                flash(f'ℹ️ تم تخطي {skipped} مقاول (موجود مسبقاً)', 'info')
            if errors:
                for error in errors:
                    flash(f'❌ {error}', 'error')
            
            return redirect(url_for('contractors.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ خطأ في الاستيراد: {str(e)}', 'error')
            return redirect(url_for('contractors.import_data'))
    
    return render_template('contractors/import.html')


@bp.route('/report')
def report():
    # Get statistics
    total_contractors = Contractor.query.count()
    
    # TODO: Add more statistics when project stages are available
    active_contractors = 0  # Placeholder
    total_projects_value = 0  # Placeholder
    
    return render_template('contractors/report.html',
                         total_contractors=total_contractors,
                         active_contractors=active_contractors,
                         total_projects_value=total_projects_value,
                         format_currency=format_currency)


def generate_excel_html(contractors):
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
        <h1>قائمة المقاولين</h1>
        <table>
            <thead>
                <tr>
                    <th>الكود</th>
                    <th>الاسم</th>
                    <th>الهاتف</th>
                    <th>البريد الإلكتروني</th>
                    <th>التخصص</th>
                    <th>العنوان</th>
                    <th>ملاحظات</th>
                    <th>تاريخ التسجيل</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for contractor in contractors:
        html += f'''
            <tr>
                <td>{contractor.code}</td>
                <td>{contractor.name}</td>
                <td>{contractor.phone or ''}</td>
                <td>{contractor.email or ''}</td>
                <td>{contractor.specialty or ''}</td>
                <td>{contractor.address or ''}</td>
                <td>{contractor.notes or ''}</td>
                <td>{contractor.created_at.strftime('%Y-%m-%d') if contractor.created_at else ''}</td>
            </tr>
        '''
    
    html += '''
            </tbody>
        </table>
    </body>
    </html>
    '''
    
    return html