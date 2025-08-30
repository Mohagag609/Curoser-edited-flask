from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.partners import bp
from acc.extensions import db
from acc.models import Partner
from acc.services.utils import generate_uid, log_action, Pagination, format_currency
from acc.services.code_generator import generate_partner_code
from sqlalchemy import or_, func

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