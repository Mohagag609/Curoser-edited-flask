from flask import render_template, request, redirect, url_for, flash, jsonify
from acc.blueprints.suppliers import bp
from acc.extensions import db
from acc.models import Supplier
from acc.services.utils import generate_uid, log_action, Pagination
from acc.services.code_generator import generate_supplier_code
from sqlalchemy import or_, func

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    
    query = Supplier.query
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Supplier.name.ilike(search_term),
                Supplier.code.ilike(search_term),
                Supplier.phone.ilike(search_term),
                Supplier.email.ilike(search_term),
                Supplier.address.ilike(search_term),
                Supplier.contact_person.ilike(search_term)
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Supplier.status == status)
    
    # Order by
    query = query.order_by(Supplier.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Calculate stats
    total_suppliers = Supplier.query.count()
    active_suppliers = Supplier.query.filter_by(status='نشط').count()
    inactive_suppliers = Supplier.query.filter_by(status='غير نشط').count()
    
    return render_template('suppliers/index.html',
                         suppliers=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status,
                         total_suppliers=total_suppliers,
                         active_suppliers=active_suppliers,
                         inactive_suppliers=inactive_suppliers)

@bp.route('/search')
def search():
    """Advanced search endpoint for AJAX"""
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    
    query = Supplier.query
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Supplier.name.ilike(search_term),
                Supplier.code.ilike(search_term),
                Supplier.phone.ilike(search_term),
                Supplier.email.ilike(search_term),
                Supplier.address.ilike(search_term),
                Supplier.contact_person.ilike(search_term)
            )
        )
    
    # Status filter
    if status:
        query = query.filter(Supplier.status == status)
    
    # Order by
    query = query.order_by(Supplier.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('suppliers/_results.html',
                             suppliers=pagination.items,
                             pagination=pagination,
                             q=q,
                             status=status)
    
    # Otherwise return full page
    return render_template('suppliers/index.html',
                         suppliers=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status)

@bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            contact_person = request.form.get('contact_person', '').strip()
            phone = request.form.get('phone', '').strip() or None
            email = request.form.get('email', '').strip() or None
            address = request.form.get('address', '').strip() or None
            status = request.form.get('status', 'نشط')
            notes = request.form.get('notes', '').strip() or None
            
            if not name:
                error_msg = 'الرجاء إدخال اسم المورد'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('suppliers.add'))
            
            # Check for duplicate name
            existing = Supplier.query.filter_by(name=name).first()
            if existing:
                error_msg = f'مورد بنفس الاسم "{name}" موجود بالفعل'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': f'⚠️ {error_msg}',
                        'redirect': url_for('suppliers.detail', id=existing.id)
                    }), 400
                
                flash(f'⚠️ {error_msg}', 'warning')
                return redirect(url_for('suppliers.detail', id=existing.id))
            
            # Generate code automatically
            code = generate_supplier_code()
            
            supplier = Supplier(
                id=generate_uid('SUP'),
                code=code,
                name=name,
                contact_person=contact_person,
                phone=phone,
                email=email,
                address=address,
                status=status,
                notes=notes
            )
            
            db.session.add(supplier)
            db.session.commit()
            
            log_action('إضافة مورد', {'id': supplier.id, 'name': supplier.name})
            
            success_msg = f'تم إضافة المورد بنجاح! رقم المورد: {code}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('suppliers.detail', id=supplier.id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('suppliers.detail', id=supplier.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء إضافة المورد: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('suppliers.add'))
    
    return render_template('suppliers/add.html')

@bp.route('/<string:id>')
def detail(id):
    supplier = Supplier.query.get_or_404(id)
    
    # Get purchase statistics
    # TODO: Add purchase orders model later
    total_purchases = 0
    pending_payments = 0
    
    return render_template('suppliers/detail.html',
                         supplier=supplier,
                         total_purchases=total_purchases,
                         pending_payments=pending_payments)

@bp.route('/<string:id>/edit', methods=['GET', 'POST'])
def edit(id):
    supplier = Supplier.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            supplier.name = request.form.get('name', '').strip()
            supplier.contact_person = request.form.get('contact_person', '').strip()
            supplier.phone = request.form.get('phone', '').strip() or None
            supplier.email = request.form.get('email', '').strip() or None
            supplier.address = request.form.get('address', '').strip() or None
            supplier.status = request.form.get('status', supplier.status)
            supplier.notes = request.form.get('notes', '').strip() or None
            
            if not supplier.name:
                error_msg = 'الرجاء إدخال اسم المورد'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('suppliers.edit', id=id))
            
            # Check for duplicate name (excluding current supplier)
            existing = Supplier.query.filter(
                Supplier.name == supplier.name,
                Supplier.id != supplier.id
            ).first()
            
            if existing:
                error_msg = f'مورد آخر بنفس الاسم "{supplier.name}" موجود بالفعل'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': f'⚠️ {error_msg}',
                        'redirect': url_for('suppliers.detail', id=existing.id)
                    }), 400
                
                flash(f'⚠️ {error_msg}', 'warning')
                return redirect(url_for('suppliers.edit', id=id))
            
            log_action('تعديل مورد', {'id': supplier.id, 'name': supplier.name})
            db.session.commit()
            
            success_msg = 'تم تعديل المورد بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('suppliers.detail', id=id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('suppliers.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء تعديل المورد: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('suppliers.edit', id=id))
    
    return render_template('suppliers/edit.html', supplier=supplier)

@bp.route('/<string:id>/delete', methods=['POST'])
def delete(id):
    try:
        supplier = Supplier.query.get_or_404(id)
        
        # TODO: Check if supplier has purchase orders
        # if supplier has orders, prevent deletion
        
        supplier_name = supplier.name
        supplier_id = supplier.id
        
        db.session.delete(supplier)
        db.session.commit()
        
        log_action('حذف مورد', {'id': supplier_id, 'name': supplier_name})
        
        success_msg = f'تم حذف المورد "{supplier_name}" بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'✅ {success_msg}'
            })
        
        flash(f'✅ {success_msg}', 'success')
        return redirect(url_for('suppliers.index'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'خطأ في حذف المورد: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
        
        flash(f'❌ {error_msg}', 'error')
        return redirect(url_for('suppliers.index'))
