from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from acc.blueprints.partners import bp
from acc.models import Partner, PartnerGroup, PartnerGroupMember, UnitPartner, PartnerDebt
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination, parse_number, format_currency
from acc.services.code_generator import generate_partner_code
from sqlalchemy import func, or_
import json
import csv
import io
from datetime import datetime


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    
    partners = Partner.query
    
    if q:
        partners = partners.filter(
            or_(
                Partner.name.contains(q),
                Partner.phone.contains(q),
                Partner.national_id.contains(q),
                Partner.address.contains(q)
            )
        )
    
    partners = partners.order_by(Partner.name)
    pagination = Pagination(partners, page)
    
    return render_template('partners/index.html', 
                         partners=pagination.items, 
                         pagination=pagination,
                         q=q)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            national_id = request.form.get('national_id', '').strip()
            address = request.form.get('address', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validate required fields
            if not name:
                flash('⚠️ الرجاء إدخال اسم الشريك', 'warning')
                return redirect(url_for('partners.add'))
            
            # Check if partner exists
            existing = Partner.query.filter_by(name=name).first()
            if existing:
                flash('⚠️ يوجد شريك بنفس الاسم', 'warning')
                return redirect(url_for('partners.add'))
            
            # Create partner with auto-generated code
            partner = Partner(
                id=generate_uid('P'),
                code=generate_partner_code(),
                name=name,
                phone=phone,
                national_id=national_id,
                address=address,
                notes=notes
            )
            
            db.session.add(partner)
            db.session.commit()
            
            # Log action
            log_action('إضافة شريك', {'id': partner.id, 'name': partner.name})
            
            flash(f'✅ تم إضافة الشريك "{partner.name}" بنجاح', 'success')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'تم إضافة الشريك "{partner.name}" بنجاح',
                    'redirect': url_for('partners.index')
                })
            
            return redirect(url_for('partners.index'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'❌ خطأ في إضافة الشريك: {str(e)}'
            flash(error_msg, 'error')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg}), 500
                
            return redirect(url_for('partners.add'))
    
    return render_template('partners/add.html')


@bp.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    partner = Partner.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            national_id = request.form.get('national_id', '').strip()
            address = request.form.get('address', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validate
            if not name:
                flash('⚠️ الرجاء إدخال اسم الشريك', 'warning')
                return redirect(url_for('partners.edit', id=id))
            
            # Check duplicate name
            existing = Partner.query.filter_by(name=name).filter(Partner.id != id).first()
            if existing:
                flash('⚠️ يوجد شريك آخر بنفس الاسم', 'warning')
                return redirect(url_for('partners.edit', id=id))
            
            # Update partner
            partner.name = name
            partner.phone = phone
            partner.national_id = national_id
            partner.address = address
            partner.notes = notes
            
            db.session.commit()
            
            # Log action
            log_action('تعديل شريك', {'id': partner.id, 'name': partner.name})
            
            flash(f'✅ تم تحديث الشريك "{partner.name}" بنجاح', 'success')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'تم تحديث الشريك "{partner.name}" بنجاح',
                    'redirect': url_for('partners.detail', id=id)
                })
            
            return redirect(url_for('partners.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'❌ خطأ في تحديث الشريك: {str(e)}'
            flash(error_msg, 'error')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg}), 500
                
            return redirect(url_for('partners.edit', id=id))
    
    return render_template('partners/edit.html', partner=partner)


@bp.route('/detail/<id>')
def detail(id):
    partner = Partner.query.get_or_404(id)
    
    # Get statistics
    total_units = partner.unit_partnerships.count()
    total_shares = db.session.query(func.sum(UnitPartner.share_percent)).filter_by(partner_id=id).scalar() or 0
    total_debts = db.session.query(func.sum(PartnerDebt.amount)).filter_by(partner_id=id).scalar() or 0
    
    # Get recent units
    recent_units = partner.unit_partnerships.order_by(UnitPartner.created_at.desc()).limit(5).all()
    
    # Get debts
    debts = partner.debts.order_by(PartnerDebt.created_at.desc()).all()
    
    return render_template('partners/detail.html', 
                         partner=partner,
                         total_units=total_units,
                         total_shares=total_shares,
                         total_debts=total_debts,
                         recent_units=recent_units,
                         debts=debts,
                         format_currency=format_currency)


@bp.route('/delete/<id>', methods=['POST'])
def delete(id):
    try:
        partner = Partner.query.get_or_404(id)
        
        # Check if has units
        if partner.unit_partnerships.count() > 0:
            flash('⚠️ لا يمكن حذف هذا الشريك لوجود وحدات مرتبطة به', 'warning')
            return redirect(url_for('partners.index'))
        
        # Check if has debts
        if partner.debts.count() > 0:
            flash('⚠️ لا يمكن حذف هذا الشريك لوجود ديون مسجلة عليه', 'warning')
            return redirect(url_for('partners.index'))
        
        # Store info before deletion
        partner_name = partner.name
        partner_id = partner.id
        
        # Delete partner
        db.session.delete(partner)
        db.session.commit()
        
        # Log action
        log_action('حذف شريك', {'id': partner_id, 'name': partner_name})
        
        flash(f'✅ تم حذف الشريك "{partner_name}" بنجاح', 'success')
        return redirect(url_for('partners.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ خطأ في حذف الشريك: {str(e)}', 'error')
        return redirect(url_for('partners.index'))


@bp.route('/export/<format>')
def export(format):
    partners = Partner.query.order_by(Partner.name).all()
    
    if format == 'excel':
        # Generate HTML table for Excel
        html = generate_excel_html(partners)
        
        response = make_response(html)
        response.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=partners_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
        
        return response
        
    elif format == 'json':
        data = [{
            'id': p.id,
            'code': p.code,
            'name': p.name,
            'phone': p.phone,
            'national_id': p.national_id,
            'address': p.address,
            'notes': p.notes,
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in partners]
        
        response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=partners_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return response
        
    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['الكود', 'الاسم', 'الهاتف', 'الرقم القومي', 'العنوان', 'ملاحظات', 'تاريخ التسجيل'])
        
        # Data
        for p in partners:
            writer.writerow([
                p.code,
                p.name,
                p.phone or '',
                p.national_id or '',
                p.address or '',
                p.notes or '',
                p.created_at.strftime('%Y-%m-%d') if p.created_at else ''
            ])
        
        response = make_response('\ufeff' + output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = f'attachment; filename=partners_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    else:
        flash('صيغة التصدير غير مدعومة', 'error')
        return redirect(url_for('partners.index'))


@bp.route('/import', methods=['GET', 'POST'])
def import_data():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file:
                flash('⚠️ الرجاء اختيار ملف', 'warning')
                return redirect(url_for('partners.import_data'))
            
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
                        if Partner.query.filter_by(name=item['name']).first():
                            skipped += 1
                            continue
                        
                        partner = Partner(
                            id=generate_uid('P'),
                            code=generate_partner_code(),
                            name=item['name'],
                            phone=item.get('phone', ''),
                            national_id=item.get('national_id', ''),
                            address=item.get('address', ''),
                            notes=item.get('notes', '')
                        )
                        db.session.add(partner)
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
                        if Partner.query.filter_by(name=name).first():
                            skipped += 1
                            continue
                        
                        partner = Partner(
                            id=generate_uid('P'),
                            code=generate_partner_code(),
                            name=name,
                            phone=row.get('الهاتف') or row.get('phone') or row.get('Phone') or '',
                            national_id=row.get('الرقم القومي') or row.get('national_id') or row.get('National ID') or '',
                            address=row.get('العنوان') or row.get('address') or row.get('Address') or '',
                            notes=row.get('ملاحظات') or row.get('notes') or row.get('Notes') or ''
                        )
                        db.session.add(partner)
                        imported += 1
                        
                except Exception as e:
                    errors.append(f'خطأ في معالجة CSV: {str(e)}')
            
            else:
                flash('⚠️ نوع الملف غير مدعوم. يرجى استخدام JSON أو CSV', 'warning')
                return redirect(url_for('partners.import_data'))
            
            if imported > 0:
                db.session.commit()
                log_action('استيراد شركاء', {'count': imported})
            
            # Show results
            if imported > 0:
                flash(f'✅ تم استيراد {imported} شريك بنجاح', 'success')
            if skipped > 0:
                flash(f'ℹ️ تم تخطي {skipped} شريك (موجود مسبقاً)', 'info')
            if errors:
                for error in errors:
                    flash(f'❌ {error}', 'error')
            
            return redirect(url_for('partners.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ خطأ في الاستيراد: {str(e)}', 'error')
            return redirect(url_for('partners.import_data'))
    
    return render_template('partners/import.html')


@bp.route('/report')
def report():
    # Get statistics
    total_partners = Partner.query.count()
    active_partners = Partner.query.join(Partner.unit_partnerships).distinct().count()
    
    # Top partners by units
    top_partners = db.session.query(
        Partner,
        func.count(UnitPartner.id).label('units_count'),
        func.sum(UnitPartner.share_percent).label('total_shares')
    ).join(Partner.unit_partnerships).group_by(Partner.id).order_by(
        func.count(UnitPartner.id).desc()
    ).limit(10).all()
    
    # Partners with debts
    partners_with_debts = db.session.query(
        Partner,
        func.sum(PartnerDebt.amount).label('total_debt')
    ).join(Partner.debts).group_by(Partner.id).order_by(
        func.sum(PartnerDebt.amount).desc()
    ).limit(10).all()
    
    return render_template('partners/report.html',
                         total_partners=total_partners,
                         active_partners=active_partners,
                         top_partners=top_partners,
                         partners_with_debts=partners_with_debts,
                         format_currency=format_currency)


# Partner Groups Routes
@bp.route('/groups')
def groups():
    groups = PartnerGroup.query.order_by(PartnerGroup.name).all()
    return render_template('partners/groups.html', groups=groups)


@bp.route('/groups/add', methods=['GET', 'POST'])
def add_group():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            
            if not name:
                flash('⚠️ الرجاء إدخال اسم المجموعة', 'warning')
                return redirect(url_for('partners.add_group'))
            
            # Check if exists
            if PartnerGroup.query.filter_by(name=name).first():
                flash('⚠️ يوجد مجموعة بنفس الاسم', 'warning')
                return redirect(url_for('partners.add_group'))
            
            group = PartnerGroup(
                id=generate_uid('PG'),
                name=name,
                description=description
            )
            
            db.session.add(group)
            db.session.commit()
            
            log_action('إضافة مجموعة شركاء', {'id': group.id, 'name': group.name})
            flash(f'✅ تم إضافة المجموعة "{group.name}" بنجاح', 'success')
            
            return redirect(url_for('partners.groups'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ خطأ في إضافة المجموعة: {str(e)}', 'error')
            return redirect(url_for('partners.add_group'))
    
    return render_template('partners/add_group.html')


# Helper function
def generate_excel_html(partners):
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
        <h1>قائمة الشركاء</h1>
        <table>
            <thead>
                <tr>
                    <th>الكود</th>
                    <th>الاسم</th>
                    <th>الهاتف</th>
                    <th>الرقم القومي</th>
                    <th>العنوان</th>
                    <th>ملاحظات</th>
                    <th>تاريخ التسجيل</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for partner in partners:
        html += f'''
            <tr>
                <td>{partner.code}</td>
                <td>{partner.name}</td>
                <td>{partner.phone or ''}</td>
                <td>{partner.national_id or ''}</td>
                <td>{partner.address or ''}</td>
                <td>{partner.notes or ''}</td>
                <td>{partner.created_at.strftime('%Y-%m-%d') if partner.created_at else ''}</td>
            </tr>
        '''
    
    html += '''
            </tbody>
        </table>
    </body>
    </html>
    '''
    
    return html