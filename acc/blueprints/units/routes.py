from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from acc.blueprints.units import bp
from acc.extensions import db
from acc.models import Unit, Partner, PartnerGroup, PartnerGroupMember, UnitPartner, Contract
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from acc.services.project_context import get_current_project, filter_by_project
from acc.services.code_generator import generate_unit_code
from sqlalchemy import or_, func
import json
import csv
import io
from datetime import datetime


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status_filter = request.args.get('status', '')
    
    # Start with filtered query by project
    query = filter_by_project(Unit.query, Unit)
    
    if q:
        query = query.filter(
            or_(
                Unit.code.contains(q),
                Unit.name.contains(q),
                Unit.floor.contains(q),
                Unit.building.contains(q)
            )
        )
    
    if status_filter:
        query = query.filter(Unit.status == status_filter)
    
    query = query.order_by(Unit.code)
    pagination = Pagination(query, page)
    
    # Get partner names for each unit
    units_data = []
    for unit in pagination.items:
        partners = []
        for up in unit.partners:
            partner = Partner.query.get(up.partner_id)
            if partner:
                partners.append(f"{partner.name} ({up.percentage}%)")
        units_data.append({
            'unit': unit,
            'partners': ', '.join(partners) if partners else 'لا يوجد شركاء',
            'remaining': unit.calculate_remaining()
        })
    
    return render_template('units/index.html',
                         units_data=units_data,
                         pagination=pagination,
                         q=q,
                         status_filter=status_filter,
                         format_currency=format_currency)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    # Get current project
    project = get_current_project()
    if not project:
        flash('⚠️ الرجاء اختيار مشروع أولاً', 'warning')
        return redirect(url_for('main.select_project'))
    
    # Check if project has units feature
    if not project.has_feature('units'):
        flash('⚠️ هذا المشروع لا يدعم إدارة الوحدات', 'warning')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            floor = request.form.get('floor', '').strip()
            building = request.form.get('building', '').strip()
            area = request.form.get('area', '0').strip()
            price = request.form.get('price', '0').strip()
            unit_type = request.form.get('unit_type', 'apartment')
            status = request.form.get('status', 'available')
            description = request.form.get('description', '').strip()
            
            # Validate required fields
            if not all([name, floor, building]):
                flash('⚠️ الرجاء ملء جميع الحقول المطلوبة', 'warning')
                return redirect(url_for('units.add'))
            
            # Generate unit code based on building, floor, and name
            code = generate_unit_code(building, floor, name)
            
            # Create unit
            unit = Unit(
                id=generate_uid('U'),
                code=code,
                project_id=project.id,
                name=name,
                floor=floor,
                building=building,
                area=float(area) if area else 0,
                price=float(price) if price else 0,
                unit_type=unit_type,
                status=status,
                description=description
            )
            
            db.session.add(unit)
            db.session.commit()
            
            # Log action
            log_action('إضافة وحدة', {'id': unit.id, 'code': unit.code, 'name': unit.name})
            
            flash(f'✅ تم إضافة الوحدة "{unit.name}" بالكود "{unit.code}" بنجاح', 'success')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'تم إضافة الوحدة "{unit.name}" بنجاح',
                    'redirect': url_for('units.detail', id=unit.id)
                })
            
            return redirect(url_for('units.detail', id=unit.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'❌ خطأ في إضافة الوحدة: {str(e)}'
            flash(error_msg, 'error')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg}), 500
                
            return redirect(url_for('units.add'))
    
    return render_template('units/add.html')


@bp.route('/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    unit = Unit.query.get_or_404(id)
    
    # Verify project access
    if unit.project_id and unit.project_id != get_current_project().id:
        flash('⚠️ لا يمكنك تعديل وحدة من مشروع آخر', 'warning')
        return redirect(url_for('units.index'))
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            floor = request.form.get('floor', '').strip()
            building = request.form.get('building', '').strip()
            area = request.form.get('area', '0').strip()
            price = request.form.get('price', '0').strip()
            unit_type = request.form.get('unit_type', 'apartment')
            status = request.form.get('status', 'available')
            description = request.form.get('description', '').strip()
            
            # Validate
            if not all([name, floor, building]):
                flash('⚠️ الرجاء ملء جميع الحقول المطلوبة', 'warning')
                return redirect(url_for('units.edit', id=id))
            
            # Update unit
            unit.name = name
            unit.floor = floor
            unit.building = building
            unit.area = float(area) if area else 0
            unit.price = float(price) if price else 0
            unit.unit_type = unit_type
            unit.status = status
            unit.description = description
            
            # Update code if building/floor/name changed
            new_code = generate_unit_code(building, floor, name)
            if new_code != unit.code:
                # Check if new code is unique
                existing = Unit.query.filter_by(code=new_code).filter(Unit.id != id).first()
                if not existing:
                    unit.code = new_code
            
            db.session.commit()
            
            # Log action
            log_action('تعديل وحدة', {'id': unit.id, 'code': unit.code, 'name': unit.name})
            
            flash(f'✅ تم تحديث الوحدة "{unit.name}" بنجاح', 'success')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'تم تحديث الوحدة "{unit.name}" بنجاح',
                    'redirect': url_for('units.detail', id=id)
                })
            
            return redirect(url_for('units.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'❌ خطأ في تحديث الوحدة: {str(e)}'
            flash(error_msg, 'error')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg}), 500
                
            return redirect(url_for('units.edit', id=id))
    
    return render_template('units/edit.html', unit=unit)


@bp.route('/detail/<id>')
def detail(id):
    unit = Unit.query.get_or_404(id)
    
    # Verify project access
    if unit.project_id and unit.project_id != get_current_project().id:
        flash('⚠️ لا يمكنك عرض وحدة من مشروع آخر', 'warning')
        return redirect(url_for('units.index'))
    
    # Get partners
    partners = []
    for up in unit.partners:
        partner = Partner.query.get(up.partner_id)
        if partner:
            partners.append({
                'partner': partner,
                'percentage': up.percentage,
                'notes': up.notes
            })
    
    # Get contract if exists
    contract = unit.contracts.first() if unit.contracts.count() > 0 else None
    
    # Calculate financials
    remaining = unit.calculate_remaining()
    total_partners_percentage = sum(p['percentage'] for p in partners)
    
    return render_template('units/detail.html',
                         unit=unit,
                         partners=partners,
                         contract=contract,
                         remaining=remaining,
                         total_partners_percentage=total_partners_percentage,
                         format_currency=format_currency)


@bp.route('/delete/<id>', methods=['POST'])
def delete(id):
    try:
        unit = Unit.query.get_or_404(id)
        
        # Verify project access
        if unit.project_id and unit.project_id != get_current_project().id:
            flash('⚠️ لا يمكنك حذف وحدة من مشروع آخر', 'warning')
            return redirect(url_for('units.index'))
        
        # Check if has contracts
        if unit.contracts.count() > 0:
            flash('⚠️ لا يمكن حذف هذه الوحدة لوجود عقود مرتبطة بها', 'warning')
            return redirect(url_for('units.index'))
        
        # Store info before deletion
        unit_name = unit.name
        unit_code = unit.code
        unit_id = unit.id
        
        # Delete unit (partners will be deleted by cascade)
        db.session.delete(unit)
        db.session.commit()
        
        # Log action
        log_action('حذف وحدة', {'id': unit_id, 'code': unit_code, 'name': unit_name})
        
        flash(f'✅ تم حذف الوحدة "{unit_name}" بنجاح', 'success')
        return redirect(url_for('units.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ خطأ في حذف الوحدة: {str(e)}', 'error')
        return redirect(url_for('units.index'))


@bp.route('/export/<format>')
def export(format):
    # Get filtered units
    query = filter_by_project(Unit.query, Unit)
    units = query.order_by(Unit.code).all()
    
    if format == 'excel':
        # Generate HTML table for Excel
        html = generate_excel_html(units)
        
        response = make_response(html)
        response.headers['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=units_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
        
        return response
        
    elif format == 'json':
        data = []
        for unit in units:
            partners = []
            for up in unit.partners:
                partner = Partner.query.get(up.partner_id)
                if partner:
                    partners.append({
                        'name': partner.name,
                        'percentage': up.percentage
                    })
            
            data.append({
                'id': unit.id,
                'code': unit.code,
                'name': unit.name,
                'building': unit.building,
                'floor': unit.floor,
                'area': unit.area,
                'price': unit.price,
                'unit_type': unit.unit_type,
                'status': unit.status,
                'description': unit.description,
                'partners': partners,
                'created_at': unit.created_at.isoformat() if unit.created_at else None
            })
        
        response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=units_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        return response
        
    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['الكود', 'الاسم', 'المبنى', 'الدور', 'المساحة', 'السعر', 'النوع', 'الحالة', 'الشركاء', 'تاريخ التسجيل'])
        
        # Data
        for unit in units:
            partners = []
            for up in unit.partners:
                partner = Partner.query.get(up.partner_id)
                if partner:
                    partners.append(f"{partner.name} ({up.percentage}%)")
            
            writer.writerow([
                unit.code,
                unit.name,
                unit.building,
                unit.floor,
                unit.area,
                unit.price,
                unit.unit_type,
                unit.status,
                ', '.join(partners),
                unit.created_at.strftime('%Y-%m-%d') if unit.created_at else ''
            ])
        
        response = make_response('\ufeff' + output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
        response.headers['Content-Disposition'] = f'attachment; filename=units_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    else:
        flash('صيغة التصدير غير مدعومة', 'error')
        return redirect(url_for('units.index'))


@bp.route('/import', methods=['GET', 'POST'])
def import_data():
    # Get current project
    project = get_current_project()
    if not project:
        flash('⚠️ الرجاء اختيار مشروع أولاً', 'warning')
        return redirect(url_for('main.select_project'))
    
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            if not file:
                flash('⚠️ الرجاء اختيار ملف', 'warning')
                return redirect(url_for('units.import_data'))
            
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
                        if not all([item.get('name'), item.get('building'), item.get('floor')]):
                            skipped += 1
                            continue
                        
                        # Generate code
                        code = generate_unit_code(item['building'], item['floor'], item['name'])
                        
                        # Check if exists
                        if Unit.query.filter_by(code=code).first():
                            skipped += 1
                            continue
                        
                        unit = Unit(
                            id=generate_uid('U'),
                            code=code,
                            project_id=project.id,
                            name=item['name'],
                            building=item['building'],
                            floor=item['floor'],
                            area=float(item.get('area', 0)),
                            price=float(item.get('price', 0)),
                            unit_type=item.get('unit_type', 'apartment'),
                            status=item.get('status', 'available'),
                            description=item.get('description', '')
                        )
                        db.session.add(unit)
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
                        building = row.get('المبنى') or row.get('building') or row.get('Building')
                        floor = row.get('الدور') or row.get('floor') or row.get('Floor')
                        
                        if not all([name, building, floor]):
                            skipped += 1
                            continue
                        
                        # Generate code
                        code = generate_unit_code(building, floor, name)
                        
                        # Check if exists
                        if Unit.query.filter_by(code=code).first():
                            skipped += 1
                            continue
                        
                        unit = Unit(
                            id=generate_uid('U'),
                            code=code,
                            project_id=project.id,
                            name=name,
                            building=building,
                            floor=floor,
                            area=float(row.get('المساحة') or row.get('area') or 0),
                            price=float(row.get('السعر') or row.get('price') or 0),
                            unit_type=row.get('النوع') or row.get('unit_type') or 'apartment',
                            status=row.get('الحالة') or row.get('status') or 'available',
                            description=row.get('الوصف') or row.get('description') or ''
                        )
                        db.session.add(unit)
                        imported += 1
                        
                except Exception as e:
                    errors.append(f'خطأ في معالجة CSV: {str(e)}')
            
            else:
                flash('⚠️ نوع الملف غير مدعوم. يرجى استخدام JSON أو CSV', 'warning')
                return redirect(url_for('units.import_data'))
            
            if imported > 0:
                db.session.commit()
                log_action('استيراد وحدات', {'count': imported})
            
            # Show results
            if imported > 0:
                flash(f'✅ تم استيراد {imported} وحدة بنجاح', 'success')
            if skipped > 0:
                flash(f'ℹ️ تم تخطي {skipped} وحدة (موجودة مسبقاً)', 'info')
            if errors:
                for error in errors:
                    flash(f'❌ {error}', 'error')
            
            return redirect(url_for('units.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ خطأ في الاستيراد: {str(e)}', 'error')
            return redirect(url_for('units.import_data'))
    
    return render_template('units/import.html')


@bp.route('/report')
def report():
    # Get current project
    project = get_current_project()
    if not project:
        flash('⚠️ الرجاء اختيار مشروع أولاً', 'warning')
        return redirect(url_for('main.select_project'))
    
    # Get statistics
    query = filter_by_project(Unit.query, Unit)
    
    total_units = query.count()
    available_units = query.filter_by(status='available').count()
    sold_units = query.filter_by(status='sold').count()
    reserved_units = query.filter_by(status='reserved').count()
    
    # Units by building
    units_by_building = db.session.query(
        Unit.building,
        func.count(Unit.id).label('count'),
        func.sum(Unit.price).label('total_value')
    ).filter(Unit.project_id == project.id).group_by(Unit.building).all()
    
    # Units by type
    units_by_type = db.session.query(
        Unit.unit_type,
        func.count(Unit.id).label('count'),
        func.avg(Unit.price).label('avg_price')
    ).filter(Unit.project_id == project.id).group_by(Unit.unit_type).all()
    
    # Total values
    total_value = query.with_entities(func.sum(Unit.price)).scalar() or 0
    total_area = query.with_entities(func.sum(Unit.area)).scalar() or 0
    
    return render_template('units/report.html',
                         total_units=total_units,
                         available_units=available_units,
                         sold_units=sold_units,
                         reserved_units=reserved_units,
                         units_by_building=units_by_building,
                         units_by_type=units_by_type,
                         total_value=total_value,
                         total_area=total_area,
                         format_currency=format_currency)


# Partner Management Routes
@bp.route('/<unit_id>/partners')
def partners(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    
    # Verify project access
    if unit.project_id and unit.project_id != get_current_project().id:
        flash('⚠️ لا يمكنك إدارة شركاء وحدة من مشروع آخر', 'warning')
        return redirect(url_for('units.index'))
    
    partners = []
    for up in unit.partners:
        partner = Partner.query.get(up.partner_id)
        if partner:
            partners.append({
                'id': up.id,
                'partner': partner,
                'percentage': up.percentage,
                'notes': up.notes
            })
    
    total_percentage = sum(p['percentage'] for p in partners)
    available_partners = Partner.query.filter(
        ~Partner.id.in_([p['partner'].id for p in partners])
    ).all()
    
    return render_template('units/partners.html',
                         unit=unit,
                         partners=partners,
                         total_percentage=total_percentage,
                         available_partners=available_partners)


# Helper function
def generate_excel_html(units):
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
            .status-available { background-color: #d4edda; color: #155724; }
            .status-sold { background-color: #f8d7da; color: #721c24; }
            .status-reserved { background-color: #fff3cd; color: #856404; }
        </style>
    </head>
    <body>
        <h1>قائمة الوحدات</h1>
        <table>
            <thead>
                <tr>
                    <th>الكود</th>
                    <th>الاسم</th>
                    <th>المبنى</th>
                    <th>الدور</th>
                    <th>المساحة (م²)</th>
                    <th>السعر</th>
                    <th>النوع</th>
                    <th>الحالة</th>
                    <th>الشركاء</th>
                    <th>تاريخ التسجيل</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    for unit in units:
        # Get partners
        partners = []
        for up in unit.partners:
            partner = Partner.query.get(up.partner_id)
            if partner:
                partners.append(f"{partner.name} ({up.percentage}%)")
        
        # Status class
        status_class = f'status-{unit.status}'
        
        # Unit type translation
        unit_types = {
            'apartment': 'شقة',
            'villa': 'فيلا',
            'shop': 'محل',
            'office': 'مكتب'
        }
        unit_type_ar = unit_types.get(unit.unit_type, unit.unit_type)
        
        # Status translation
        statuses = {
            'available': 'متاح',
            'sold': 'مباع',
            'reserved': 'محجوز'
        }
        status_ar = statuses.get(unit.status, unit.status)
        
        html += f'''
            <tr>
                <td>{unit.code}</td>
                <td>{unit.name}</td>
                <td>{unit.building}</td>
                <td>{unit.floor}</td>
                <td>{unit.area}</td>
                <td>{unit.price:,.2f}</td>
                <td>{unit_type_ar}</td>
                <td class="{status_class}">{status_ar}</td>
                <td>{', '.join(partners) if partners else 'لا يوجد'}</td>
                <td>{unit.created_at.strftime('%Y-%m-%d') if unit.created_at else ''}</td>
            </tr>
        '''
    
    html += '''
            </tbody>
        </table>
    </body>
    </html>
    '''
    
    return html