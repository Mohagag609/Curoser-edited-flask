from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.contractors import bp
from acc.extensions import db
from acc.models import Contractor
from acc.services.utils import generate_uid, log_action, Pagination
from acc.services.code_generator import generate_contractor_code
from sqlalchemy import or_, func

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    
    query = Contractor.query
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Contractor.name.ilike(search_term),
                Contractor.code.ilike(search_term),
                Contractor.phone.ilike(search_term),
                Contractor.email.ilike(search_term),
                Contractor.address.ilike(search_term),
                Contractor.specialization.ilike(search_term)
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Contractor.status == status)
    
    # Order by
    query = query.order_by(Contractor.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Calculate stats
    total_contractors = Contractor.query.count()
    active_contractors = Contractor.query.filter_by(status='نشط').count()
    inactive_contractors = Contractor.query.filter_by(status='غير نشط').count()
    
    return render_template('contractors/index.html',
                         contractors=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status,
                         total_contractors=total_contractors,
                         active_contractors=active_contractors,
                         inactive_contractors=inactive_contractors)

@bp.route('/search')
def search():
    """Advanced search endpoint for AJAX"""
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    query = Contractor.query
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Contractor.name.ilike(search_term),
                Contractor.code.ilike(search_term),
                Contractor.phone.ilike(search_term),
                Contractor.email.ilike(search_term),
                Contractor.address.ilike(search_term),
                Contractor.specialization.ilike(search_term)
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Contractor.status == status)
    
    # Order by
    query = query.order_by(Contractor.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('contractors/_results.html',
                             contractors=pagination.items,
                             pagination=pagination,
                             q=q,
                             status=status)
    
    # Otherwise return full page
    return render_template('contractors/index.html',
                         contractors=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip() or None
            email = request.form.get('email', '').strip() or None
            address = request.form.get('address', '').strip() or None
            specialization = request.form.get('specialization', '').strip() or None
            status = request.form.get('status', 'نشط')
            notes = request.form.get('notes', '').strip() or None
            
            if not name:
                error_msg = 'الرجاء إدخال اسم المقاول'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('contractors.add'))
            
            # Check for duplicate name
            existing = Contractor.query.filter_by(name=name).first()
            if existing:
                error_msg = f'مقاول بنفس الاسم "{name}" موجود بالفعل'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': f'⚠️ {error_msg}',
                        'redirect': url_for('contractors.detail', id=existing.id)
                    }), 400
                
                flash(f'⚠️ {error_msg}', 'warning')
                return redirect(url_for('contractors.detail', id=existing.id))
            
            # Generate code automatically
            code = generate_contractor_code()
            
            contractor = Contractor(
                id=generate_uid('CON'),
                code=code,
                name=name,
                phone=phone,
                email=email,
                address=address,
                specialization=specialization,
                status=status,
                notes=notes
            )
            
            db.session.add(contractor)
            db.session.commit()
            
            log_action('إضافة مقاول', {'id': contractor.id, 'name': contractor.name})
            
            success_msg = f'تم إضافة المقاول بنجاح! رقم المقاول: {code}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('contractors.detail', id=contractor.id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('contractors.detail', id=contractor.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء إضافة المقاول: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('contractors.add'))
    
    return render_template('contractors/add.html')

@bp.route('/<string:id>')
def detail(id):
    contractor = Contractor.query.get_or_404(id)
    
    # Get project statistics
    active_projects = len([s for s in contractor.stages if s.status == 'active'])
    completed_projects = len([s for s in contractor.stages if s.status == 'completed'])
    
    return render_template('contractors/detail.html',
                         contractor=contractor,
                         active_projects=active_projects,
                         completed_projects=completed_projects)

@bp.route('/<string:id>/edit', methods=['GET', 'POST'])
def edit(id):
    contractor = Contractor.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            contractor.name = request.form.get('name', '').strip()
            contractor.phone = request.form.get('phone', '').strip() or None
            contractor.email = request.form.get('email', '').strip() or None
            contractor.address = request.form.get('address', '').strip() or None
            contractor.specialization = request.form.get('specialization', '').strip() or None
            contractor.status = request.form.get('status', contractor.status)
            contractor.notes = request.form.get('notes', '').strip() or None
            
            if not contractor.name:
                error_msg = 'الرجاء إدخال اسم المقاول'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('contractors.edit', id=id))
            
            # Check for duplicate name (excluding current contractor)
            existing = Contractor.query.filter(
                Contractor.name == contractor.name,
                Contractor.id != contractor.id
            ).first()
            
            if existing:
                error_msg = f'مقاول آخر بنفس الاسم "{contractor.name}" موجود بالفعل'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': f'⚠️ {error_msg}',
                        'redirect': url_for('contractors.detail', id=existing.id)
                    }), 400
                
                flash(f'⚠️ {error_msg}', 'warning')
                return redirect(url_for('contractors.edit', id=id))
            
            log_action('تعديل مقاول', {'id': contractor.id, 'name': contractor.name})
            db.session.commit()
            
            success_msg = 'تم تعديل المقاول بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('contractors.detail', id=id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('contractors.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء تعديل المقاول: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('contractors.edit', id=id))
    
    return render_template('contractors/edit.html', contractor=contractor)

@bp.route('/<string:id>/delete', methods=['POST'])
def delete(id):
    try:
        contractor = Contractor.query.get_or_404(id)
        
        # Check if contractor has project stages
        if contractor.stages.count() > 0:
            error_msg = f'لا يمكن حذف المقاول "{contractor.name}" لوجود مراحل مشاريع مرتبطة به'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('contractors.index'))
        
        contractor_name = contractor.name
        contractor_id = contractor.id
        
        db.session.delete(contractor)
        db.session.commit()
        
        log_action('حذف مقاول', {'id': contractor_id, 'name': contractor_name})
        
        success_msg = f'تم حذف المقاول "{contractor_name}" بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'✅ {success_msg}'
            })
        
        flash(f'✅ {success_msg}', 'success')
        return redirect(url_for('contractors.index'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'خطأ في حذف المقاول: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
        
        flash(f'❌ {error_msg}', 'error')
        return redirect(url_for('contractors.index'))

@bp.route('/report')
def report():
    """Generate contractors report"""
    # Get filters
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Contractor.query
    
    # Apply filters
    if status:
        query = query.filter(Contractor.status == status)
    
    if date_from:
        query = query.filter(Contractor.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        query = query.filter(Contractor.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    contractors = query.order_by(Contractor.name).all()
    
    # Calculate statistics
    total_contractors = len(contractors)
    active_contractors = len([c for c in contractors if c.status == 'نشط'])
    inactive_contractors = len([c for c in contractors if c.status == 'غير نشط'])
    
    return render_template('contractors/report.html',
                         contractors=contractors,
                         total_contractors=total_contractors,
                         active_contractors=active_contractors,
                         inactive_contractors=inactive_contractors,
                         status=status,
                         date_from=date_from,
                         date_to=date_to)