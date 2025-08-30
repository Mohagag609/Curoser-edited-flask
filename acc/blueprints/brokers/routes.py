from flask import render_template, request, redirect, url_for, flash, jsonify, Response, send_file
from acc.blueprints.brokers import bp
from acc.extensions import db
from acc.models import Broker
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from acc.services.code_generator import generate_broker_code
from sqlalchemy import or_, func
import json
import csv
import io
from datetime import datetime


@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    
    query = Broker.query
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Broker.name.ilike(search_term),
                Broker.code.ilike(search_term),
                Broker.phone.ilike(search_term),
                Broker.national_id.ilike(search_term),
                Broker.address.ilike(search_term)
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Broker.status == status)
    
    # Order by
    query = query.order_by(Broker.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Calculate stats
    total_brokers = Broker.query.count()
    active_brokers = Broker.query.filter_by(status='نشط').count()
    inactive_brokers = Broker.query.filter_by(status='غير نشط').count()
    
    return render_template('brokers/index.html',
                         brokers=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status,
                         total_brokers=total_brokers,
                         active_brokers=active_brokers,
                         inactive_brokers=inactive_brokers)


@bp.route('/search')
def search():
    """Advanced search endpoint for AJAX"""
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    query = Broker.query
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Broker.name.ilike(search_term),
                Broker.code.ilike(search_term),
                Broker.phone.ilike(search_term),
                Broker.national_id.ilike(search_term),
                Broker.address.ilike(search_term)
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Broker.status == status)
    
    # Order by
    query = query.order_by(Broker.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('brokers/_results.html',
                             brokers=pagination.items,
                             pagination=pagination,
                             q=q,
                             status=status)
    
    # Otherwise return full page
    return render_template('brokers/index.html',
                         brokers=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip() or None
            national_id = request.form.get('national_id', '').strip() or None
            address = request.form.get('address', '').strip() or None
            commission_percentage = float(request.form.get('commission_percentage', 0))
            status = request.form.get('status', 'نشط')
            notes = request.form.get('notes', '').strip() or None
            
            if not name:
                error_msg = 'الرجاء إدخال اسم الوسيط'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('brokers.add'))
            
            # Check for duplicate name
            existing = Broker.query.filter_by(name=name).first()
            if existing:
                error_msg = f'وسيط بنفس الاسم "{name}" موجود بالفعل'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': f'⚠️ {error_msg}',
                        'redirect': url_for('brokers.detail', id=existing.id)
                    }), 400
                
                flash(f'⚠️ {error_msg}', 'warning')
                return redirect(url_for('brokers.detail', id=existing.id))
            
            # Generate code automatically
            code = generate_broker_code()
            
            broker = Broker(
                id=generate_uid('BRK'),
                code=code,
                name=name,
                phone=phone,
                national_id=national_id,
                address=address,
                commission_percentage=commission_percentage,
                status=status,
                notes=notes
            )
            
            db.session.add(broker)
            db.session.commit()
            
            log_action('إضافة وسيط', {'id': broker.id, 'name': broker.name})
            
            success_msg = f'تم إضافة الوسيط بنجاح! رقم الوسيط: {code}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('brokers.detail', id=broker.id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('brokers.detail', id=broker.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء إضافة الوسيط: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('brokers.add'))
    
    return render_template('brokers/add.html')


@bp.route('/<string:id>')
def detail(id):
    broker = Broker.query.get_or_404(id)
    
    # Get commission statistics
    total_commissions = 0
    pending_commissions = 0
    total_contracts = broker.contracts.count()
    
    return render_template('brokers/detail.html',
                         broker=broker,
                         total_commissions=total_commissions,
                         pending_commissions=pending_commissions,
                         total_contracts=total_contracts,
                         format_currency=format_currency)


@bp.route('/<string:id>/edit', methods=['GET', 'POST'])
def edit(id):
    broker = Broker.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            broker.name = request.form.get('name', '').strip()
            broker.phone = request.form.get('phone', '').strip() or None
            broker.national_id = request.form.get('national_id', '').strip() or None
            broker.address = request.form.get('address', '').strip() or None
            broker.commission_percentage = float(request.form.get('commission_percentage', broker.commission_percentage))
            broker.status = request.form.get('status', broker.status)
            broker.notes = request.form.get('notes', '').strip() or None
            
            if not broker.name:
                error_msg = 'الرجاء إدخال اسم الوسيط'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('brokers.edit', id=id))
            
            # Check for duplicate name (excluding current broker)
            existing = Broker.query.filter(
                Broker.name == broker.name,
                Broker.id != broker.id
            ).first()
            
            if existing:
                error_msg = f'وسيط آخر بنفس الاسم "{broker.name}" موجود بالفعل'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': f'⚠️ {error_msg}',
                        'redirect': url_for('brokers.detail', id=existing.id)
                    }), 400
                
                flash(f'⚠️ {error_msg}', 'warning')
                return redirect(url_for('brokers.edit', id=id))
            
            log_action('تعديل وسيط', {'id': broker.id, 'name': broker.name})
            db.session.commit()
            
            success_msg = 'تم تعديل الوسيط بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('brokers.detail', id=id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('brokers.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء تعديل الوسيط: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('brokers.edit', id=id))
    
    return render_template('brokers/edit.html', broker=broker)


@bp.route('/<string:id>/delete', methods=['POST'])
def delete(id):
    try:
        broker = Broker.query.get_or_404(id)
        
        # Check if broker has contracts
        if broker.contracts.count() > 0:
            error_msg = f'لا يمكن حذف الوسيط "{broker.name}" لوجود عقود مرتبطة به'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('brokers.index'))
        
        broker_name = broker.name
        broker_id = broker.id
        
        db.session.delete(broker)
        db.session.commit()
        
        log_action('حذف وسيط', {'id': broker_id, 'name': broker_name})
        
        success_msg = f'تم حذف الوسيط "{broker_name}" بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'✅ {success_msg}'
            })
        
        flash(f'✅ {success_msg}', 'success')
        return redirect(url_for('brokers.index'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'خطأ في حذف الوسيط: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
        
        flash(f'❌ {error_msg}', 'error')
        return redirect(url_for('brokers.index'))


@bp.route('/import', methods=['GET', 'POST'])
def import_data():
    """Import brokers from file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('❌ الرجاء اختيار ملف', 'error')
            return redirect(url_for('brokers.import_data'))
        
        file = request.files['file']
        if file.filename == '':
            flash('❌ الرجاء اختيار ملف', 'error')
            return redirect(url_for('brokers.import_data'))
        
        try:
            # تم تعطيل الاستيراد مؤقتاً - يحتاج لتحديث للنظام الجديد
            flash('❌ نظام الاستيراد قيد التحديث', 'error')
            return redirect(url_for('brokers.index'))
            
            # handler = ImportHandler()
            # data, error = handler.read_file(file)
            
            if False:  # error:
                flash(f'❌ خطأ في قراءة الملف: {error}', 'error')
                return redirect(url_for('brokers.import_data'))
            
            # Process data
            success_count = 0
            error_count = 0
            errors = []
            
            for row in data:
                try:
                    # Check required fields
                    if not row.get('name'):
                        error_count += 1
                        errors.append(f"السطر {data.index(row) + 1}: اسم الوسيط مطلوب")
                        continue
                    
                    # Check for duplicates
                    existing = Broker.query.filter_by(name=row['name']).first()
                    if existing:
                        error_count += 1
                        errors.append(f"السطر {data.index(row) + 1}: الوسيط '{row['name']}' موجود بالفعل")
                        continue
                    
                    # Create broker
                    broker = Broker(
                        id=generate_uid('BRK'),
                        code=row.get('code') or generate_broker_code(),
                        name=row['name'],
                        phone=row.get('phone'),
                        national_id=row.get('national_id'),
                        address=row.get('address'),
                        commission_percentage=float(row.get('commission_percentage', 0)),
                        status=row.get('status', 'نشط'),
                        notes=row.get('notes')
                    )
                    
                    db.session.add(broker)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"السطر {data.index(row) + 1}: {str(e)}")
            
            if success_count > 0:
                db.session.commit()
                log_action('استيراد وسطاء', {'count': success_count})
            
            return render_template('brokers/import_result.html',
                                 success_count=success_count,
                                 error_count=error_count,
                                 errors=errors)
            
        except Exception as e:
            flash(f'❌ خطأ في معالجة الملف: {str(e)}', 'error')
            return redirect(url_for('brokers.import_data'))
    
    return render_template('brokers/import.html')


@bp.route('/export')
def export():
    """Export brokers"""
    format = request.args.get('format', 'excel')
    
    brokers = Broker.query.order_by(Broker.name).all()
    
    if format == 'json':
        # JSON export
        data = []
        for broker in brokers:
            data.append({
                'code': broker.code,
                'name': broker.name,
                'phone': broker.phone or '',
                'national_id': broker.national_id or '',
                'address': broker.address or '',
                'commission_percentage': broker.commission_percentage,
                'status': broker.status,
                'notes': broker.notes or ''
            })
        
        output = io.StringIO()
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment;filename=brokers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )
    
    elif format == 'csv':
        # CSV export
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['الكود', 'الاسم', 'الهاتف', 'الرقم القومي', 'العنوان', 'نسبة العمولة', 'الحالة', 'ملاحظات'])
        
        # Data
        for broker in brokers:
            writer.writerow([
                broker.code,
                broker.name,
                broker.phone or '',
                broker.national_id or '',
                broker.address or '',
                broker.commission_percentage,
                broker.status,
                broker.notes or ''
            ])
        
        output.seek(0)
        output_bytes = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        
        return Response(
            output_bytes.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment;filename=brokers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
    
    else:
        # Excel export (HTML table)
        return render_template('brokers/export_excel.html', brokers=brokers, datetime=datetime)


@bp.route('/report')
def report():
    """Generate brokers report"""
    # Get filters
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Broker.query
    
    # Apply filters
    if status:
        query = query.filter(Broker.status == status)
    
    if date_from:
        query = query.filter(Broker.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        query = query.filter(Broker.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    brokers = query.order_by(Broker.name).all()
    
    # Calculate statistics
    total_brokers = len(brokers)
    active_brokers = len([b for b in brokers if b.status == 'نشط'])
    inactive_brokers = len([b for b in brokers if b.status == 'غير نشط'])
    total_commissions = sum(b.commission_percentage for b in brokers)
    
    return render_template('brokers/report.html',
                         brokers=brokers,
                         total_brokers=total_brokers,
                         active_brokers=active_brokers,
                         inactive_brokers=inactive_brokers,
                         total_commissions=total_commissions,
                         status=status,
                         date_from=date_from,
                         date_to=date_to)