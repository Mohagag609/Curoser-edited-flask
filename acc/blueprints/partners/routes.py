from flask import render_template, request, redirect, url_for, flash, jsonify, Response, send_file
from acc.blueprints.partners import bp
from acc.extensions import db
from acc.models import Partner
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from acc.services.code_generator import generate_partner_code
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
    
    query = Partner.query
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Partner.name.ilike(search_term),
                Partner.code.ilike(search_term),
                Partner.phone.ilike(search_term),
                Partner.national_id.ilike(search_term),
                Partner.address.ilike(search_term)
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Partner.status == status)
    
    # Order by
    query = query.order_by(Partner.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Calculate stats
    total_partners = Partner.query.count()
    active_partners = Partner.query.filter_by(status='نشط').count()
    inactive_partners = Partner.query.filter_by(status='غير نشط').count()
    
    return render_template('partners/index.html',
                         partners=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status,
                         total_partners=total_partners,
                         active_partners=active_partners,
                         inactive_partners=inactive_partners)


@bp.route('/search')
def search():
    """Advanced search endpoint for AJAX"""
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    query = Partner.query
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Partner.name.ilike(search_term),
                Partner.code.ilike(search_term),
                Partner.phone.ilike(search_term),
                Partner.national_id.ilike(search_term),
                Partner.address.ilike(search_term)
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Partner.status == status)
    
    # Order by
    query = query.order_by(Partner.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('partners/_results.html',
                             partners=pagination.items,
                             pagination=pagination,
                             q=q,
                             status=status)
    
    # Otherwise return full page
    return render_template('partners/index.html',
                         partners=pagination.items,
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
            share_percentage = float(request.form.get('share_percentage', 0))
            status = request.form.get('status', 'نشط')
            notes = request.form.get('notes', '').strip() or None
            
            if not name:
                error_msg = 'الرجاء إدخال اسم الشريك'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('partners.add'))
            
            # Check for duplicate name
            existing = Partner.query.filter_by(name=name).first()
            if existing:
                error_msg = f'شريك بنفس الاسم "{name}" موجود بالفعل'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': f'⚠️ {error_msg}',
                        'redirect': url_for('partners.detail', id=existing.id)
                    }), 400
                
                flash(f'⚠️ {error_msg}', 'warning')
                return redirect(url_for('partners.detail', id=existing.id))
            
            # Generate code automatically
            code = generate_partner_code()
            
            partner = Partner(
                id=generate_uid('PRT'),
                code=code,
                name=name,
                phone=phone,
                national_id=national_id,
                address=address,
                share_percentage=share_percentage,
                status=status,
                notes=notes
            )
            
            db.session.add(partner)
            db.session.commit()
            
            log_action('إضافة شريك', {'id': partner.id, 'name': partner.name})
            
            success_msg = f'تم إضافة الشريك بنجاح! رقم الشريك: {code}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('partners.detail', id=partner.id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('partners.detail', id=partner.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء إضافة الشريك: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('partners.add'))
    
    return render_template('partners/add.html')


@bp.route('/<string:id>')
def detail(id):
    partner = Partner.query.get_or_404(id)
    
    # Get partnership statistics
    # TODO: Calculate from phase partners
    total_share_value = 0
    pending_payments = 0
    
    return render_template('partners/detail.html',
                         partner=partner,
                         total_share_value=total_share_value,
                         pending_payments=pending_payments,
                         format_currency=format_currency)


@bp.route('/<string:id>/edit', methods=['GET', 'POST'])
def edit(id):
    partner = Partner.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            partner.name = request.form.get('name', '').strip()
            partner.phone = request.form.get('phone', '').strip() or None
            partner.national_id = request.form.get('national_id', '').strip() or None
            partner.address = request.form.get('address', '').strip() or None
            partner.share_percentage = float(request.form.get('share_percentage', partner.share_percentage))
            partner.status = request.form.get('status', partner.status)
            partner.notes = request.form.get('notes', '').strip() or None
            
            if not partner.name:
                error_msg = 'الرجاء إدخال اسم الشريك'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('partners.edit', id=id))
            
            # Check for duplicate name (excluding current partner)
            existing = Partner.query.filter(
                Partner.name == partner.name,
                Partner.id != partner.id
            ).first()
            
            if existing:
                error_msg = f'شريك آخر بنفس الاسم "{partner.name}" موجود بالفعل'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': f'⚠️ {error_msg}',
                        'redirect': url_for('partners.detail', id=existing.id)
                    }), 400
                
                flash(f'⚠️ {error_msg}', 'warning')
                return redirect(url_for('partners.edit', id=id))
            
            log_action('تعديل شريك', {'id': partner.id, 'name': partner.name})
            db.session.commit()
            
            success_msg = 'تم تعديل الشريك بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('partners.detail', id=id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('partners.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء تعديل الشريك: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('partners.edit', id=id))
    
    return render_template('partners/edit.html', partner=partner)


@bp.route('/<string:id>/delete', methods=['POST'])
def delete(id):
    try:
        partner = Partner.query.get_or_404(id)
        
        # TODO: Check if partner has phase partnerships
        
        partner_name = partner.name
        partner_id = partner.id
        
        db.session.delete(partner)
        db.session.commit()
        
        log_action('حذف شريك', {'id': partner_id, 'name': partner_name})
        
        success_msg = f'تم حذف الشريك "{partner_name}" بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'✅ {success_msg}'
            })
        
        flash(f'✅ {success_msg}', 'success')
        return redirect(url_for('partners.index'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'خطأ في حذف الشريك: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
        
        flash(f'❌ {error_msg}', 'error')
        return redirect(url_for('partners.index'))


@bp.route('/import', methods=['GET', 'POST'])
def import_data():
    """Import partners from file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('❌ الرجاء اختيار ملف', 'error')
            return redirect(url_for('partners.import_data'))
        
        file = request.files['file']
        if file.filename == '':
            flash('❌ الرجاء اختيار ملف', 'error')
            return redirect(url_for('partners.import_data'))
        
        try:
            # تم تعطيل الاستيراد مؤقتاً - يحتاج لتحديث للنظام الجديد
            flash('❌ نظام الاستيراد قيد التحديث', 'error')
            return redirect(url_for('partners.index'))
            
            # handler = ImportHandler()
            # data, error = handler.read_file(file)
            
            if False:  # error:
                flash(f'❌ خطأ في قراءة الملف: {error}', 'error')
                return redirect(url_for('partners.import_data'))
            
            # Process data
            success_count = 0
            error_count = 0
            errors = []
            
            for row in data:
                try:
                    # Check required fields
                    if not row.get('name'):
                        error_count += 1
                        errors.append(f"السطر {data.index(row) + 1}: اسم الشريك مطلوب")
                        continue
                    
                    # Check for duplicates
                    existing = Partner.query.filter_by(name=row['name']).first()
                    if existing:
                        error_count += 1
                        errors.append(f"السطر {data.index(row) + 1}: الشريك '{row['name']}' موجود بالفعل")
                        continue
                    
                    # Create partner
                    partner = Partner(
                        id=generate_uid('PRT'),
                        code=row.get('code') or generate_partner_code(),
                        name=row['name'],
                        phone=row.get('phone'),
                        national_id=row.get('national_id'),
                        address=row.get('address'),
                        share_percentage=float(row.get('share_percentage', 0)),
                        status=row.get('status', 'نشط'),
                        notes=row.get('notes')
                    )
                    
                    db.session.add(partner)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"السطر {data.index(row) + 1}: {str(e)}")
            
            if success_count > 0:
                db.session.commit()
                log_action('استيراد شركاء', {'count': success_count})
            
            return render_template('partners/import_result.html',
                                 success_count=success_count,
                                 error_count=error_count,
                                 errors=errors)
            
        except Exception as e:
            flash(f'❌ خطأ في معالجة الملف: {str(e)}', 'error')
            return redirect(url_for('partners.import_data'))
    
    return render_template('partners/import.html')


@bp.route('/export')
def export():
    """Export partners"""
    format = request.args.get('format', 'excel')
    
    partners = Partner.query.order_by(Partner.name).all()
    
    if format == 'json':
        # JSON export
        data = []
        for partner in partners:
            data.append({
                'code': partner.code,
                'name': partner.name,
                'phone': partner.phone or '',
                'national_id': partner.national_id or '',
                'address': partner.address or '',
                'share_percentage': partner.share_percentage,
                'status': partner.status,
                'notes': partner.notes or ''
            })
        
        output = io.StringIO()
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment;filename=partners_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )
    
    elif format == 'csv':
        # CSV export
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['الكود', 'الاسم', 'الهاتف', 'الرقم القومي', 'العنوان', 'نسبة الشراكة', 'الحالة', 'ملاحظات'])
        
        # Data
        for partner in partners:
            writer.writerow([
                partner.code,
                partner.name,
                partner.phone or '',
                partner.national_id or '',
                partner.address or '',
                partner.share_percentage,
                partner.status,
                partner.notes or ''
            ])
        
        output.seek(0)
        output_bytes = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        
        return Response(
            output_bytes.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment;filename=partners_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
    
    else:
        # Excel export (HTML table)
        return render_template('partners/export_excel.html', partners=partners, datetime=datetime)


@bp.route('/report')
def report():
    """Generate partners report"""
    # Get filters
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Partner.query
    
    # Apply filters
    if status:
        query = query.filter(Partner.status == status)
    
    if date_from:
        query = query.filter(Partner.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        query = query.filter(Partner.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    partners = query.order_by(Partner.name).all()
    
    # Calculate statistics
    total_partners = len(partners)
    active_partners = len([p for p in partners if p.status == 'نشط'])
    inactive_partners = len([p for p in partners if p.status == 'غير نشط'])
    total_shares = sum(p.share_percentage for p in partners)
    
    return render_template('partners/report.html',
                         partners=partners,
                         total_partners=total_partners,
                         active_partners=active_partners,
                         inactive_partners=inactive_partners,
                         total_shares=total_shares,
                         status=status,
                         date_from=date_from,
                         date_to=date_to)