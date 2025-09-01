from flask import render_template, request, redirect, url_for, flash, jsonify, Response, g
from acc.blueprints.treasury import bp
from acc.extensions import db
from acc.models import Safe, Voucher, Contract, Installment
from acc.services.utils import generate_uid, log_action, Pagination, format_currency, format_date
from acc.services.code_generator import generate_safe_code, generate_voucher_code
from sqlalchemy import or_, func
import json
import csv
import io
from datetime import datetime, date
from decimal import Decimal

@bp.route('/safes')
def safes_index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    
    query = Safe.query.filter_by(project_id=g.project.id)
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Safe.name.ilike(search_term),
                Safe.description.ilike(search_term)
            )
        )
    
    # Order by
    query = query.order_by(Safe.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Calculate stats
    total_safes = Safe.query.filter_by(project_id=g.project.id).count()
    total_balance = db.session.query(func.sum(Safe.balance)).filter_by(project_id=g.project.id).scalar() or 0
    
    return render_template('treasury/safes/index.html',
                         safes=pagination.items,
                         pagination=pagination,
                         q=q,
                         total_safes=total_safes,
                         total_balance=total_balance,
                         format_currency=format_currency)

@bp.route('/safes/search')
def safes_search():
    """Advanced search endpoint for AJAX"""
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    query = Safe.query.filter_by(project_id=g.project.id)
    
    # Text search
    if q:
        search_term = f'%{q}%'
        query = query.filter(
            or_(
                Safe.name.ilike(search_term),
                Safe.description.ilike(search_term)
            )
        )
    
    # Order by
    query = query.order_by(Safe.created_at.desc())
    
    # Pagination
    pagination = Pagination(query, page, per_page=20)
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('treasury/safes/_results.html',
                             safes=pagination.items,
                             pagination=pagination,
                             q=q,
                             format_currency=format_currency)
    
    # Otherwise return full page
    return render_template('treasury/safes/index.html',
                         safes=pagination.items,
                         pagination=pagination,
                         q=q,
                         format_currency=format_currency)

@bp.route('/safes/add', methods=['GET', 'POST'])
def safes_add():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip() or None
            initial_balance = Decimal(request.form.get('initial_balance', 0))
            
            if not name:
                error_msg = 'الرجاء إدخال اسم الخزينة'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('treasury.safes_add'))
            
            # Check for duplicate name in same project
            existing = Safe.query.filter_by(name=name, project_id=g.project.id).first()
            if existing:
                error_msg = f'خزينة بنفس الاسم "{name}" موجودة بالفعل في هذا المشروع'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': f'⚠️ {error_msg}',
                        'redirect': url_for('treasury.safes_detail', id=existing.id)
                    }), 400
                
                flash(f'⚠️ {error_msg}', 'warning')
                return redirect(url_for('treasury.safes_detail', id=existing.id))
            
            # Auto generate code if not provided
            code = generate_safe_code()
            
            safe = Safe(
                id=generate_uid('SAF'),
                name=f"{code} - {name}",  # Combine code with name
                project_id=g.project.id,
                balance=initial_balance,
                description=description
            )
            
            db.session.add(safe)
            
            # Create initial voucher if balance > 0
            if initial_balance > 0:
                voucher = Voucher(
                    id=generate_uid('VOU'),
                    code=generate_voucher_code('receipt'),
                    project_id=g.project.id,
                    type='receipt',
                    date=date.today(),
                    amount=initial_balance,
                    safe_id=safe.id,
                    description='رصيد افتتاحي',
                    payment_method='نقدي'
                )
                db.session.add(voucher)
                log_action('إيصال قبض - رصيد افتتاحي', {'safe_id': safe.id, 'amount': float(initial_balance)})
            
            db.session.commit()
            
            log_action('إضافة خزينة', {'id': safe.id, 'name': safe.name})
            
            success_msg = f'تم إضافة الخزينة بنجاح! الكود: {code}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('treasury.safes_detail', id=safe.id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('treasury.safes_detail', id=safe.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء إضافة الخزينة: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('treasury.safes_add'))
    
    return render_template('treasury/safes/add.html')

@bp.route('/safes/<string:id>')
def safes_detail(id):
    safe = Safe.query.get_or_404(id)
    
    # Ensure safe belongs to current project
    if safe.project_id != g.project.id:
        flash('❌ خزينة غير موجودة', 'error')
        return redirect(url_for('treasury.safes_index'))
    
    # Get recent transactions
    recent_vouchers = safe.vouchers.order_by(Voucher.date.desc(), Voucher.created_at.desc()).limit(10).all()
    
    # Calculate statistics
    total_receipts = db.session.query(func.sum(Voucher.amount)).filter_by(
        safe_id=safe.id, type='receipt'
    ).scalar() or 0
    
    total_payments = db.session.query(func.sum(Voucher.amount)).filter_by(
        safe_id=safe.id, type='payment'
    ).scalar() or 0
    
    return render_template('treasury/safes/detail.html',
                         safe=safe,
                         recent_vouchers=recent_vouchers,
                         total_receipts=total_receipts,
                         total_payments=total_payments,
                         format_currency=format_currency,
                         format_date=format_date)

@bp.route('/safes/<string:id>/edit', methods=['GET', 'POST'])
def safes_edit(id):
    safe = Safe.query.get_or_404(id)
    
    # Ensure safe belongs to current project
    if safe.project_id != g.project.id:
        flash('❌ خزينة غير موجودة', 'error')
        return redirect(url_for('treasury.safes_index'))
    
    if request.method == 'POST':
        try:
            # Extract name without code prefix
            name = request.form.get('name', '').strip()
            if ' - ' in safe.name:
                code = safe.name.split(' - ')[0]
                safe.name = f"{code} - {name}"
            else:
                safe.name = name
            
            safe.description = request.form.get('description', '').strip() or None
            
            if not name:
                error_msg = 'الرجاء إدخال اسم الخزينة'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
                flash(f'❌ {error_msg}', 'error')
                return redirect(url_for('treasury.safes_edit', id=id))
            
            # Check for duplicate name (excluding current safe)
            existing = Safe.query.filter(
                Safe.name == safe.name,
                Safe.project_id == g.project.id,
                Safe.id != safe.id
            ).first()
            
            if existing:
                error_msg = f'خزينة أخرى بنفس الاسم "{name}" موجودة بالفعل في هذا المشروع'
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': False,
                        'message': f'⚠️ {error_msg}',
                        'redirect': url_for('treasury.safes_detail', id=existing.id)
                    }), 400
                
                flash(f'⚠️ {error_msg}', 'warning')
                return redirect(url_for('treasury.safes_edit', id=id))
            
            log_action('تعديل خزينة', {'id': safe.id, 'name': safe.name})
            db.session.commit()
            
            success_msg = 'تم تعديل الخزينة بنجاح'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ {success_msg}',
                    'redirect': url_for('treasury.safes_detail', id=id)
                })
            
            flash(f'✅ {success_msg}', 'success')
            return redirect(url_for('treasury.safes_detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'حدث خطأ أثناء تعديل الخزينة: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
            
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('treasury.safes_edit', id=id))
    
    # Extract name without code for editing
    name = safe.name
    if ' - ' in name:
        name = name.split(' - ', 1)[1]
    
    return render_template('treasury/safes/edit.html', safe=safe, name=name)

@bp.route('/safes/<string:id>/delete', methods=['POST'])
def safes_delete(id):
    try:
        safe = Safe.query.get_or_404(id)
        
        # Ensure safe belongs to current project
        if safe.project_id != g.project.id:
            error_msg = 'خزينة غير موجودة'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 404
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('treasury.safes_index'))
        
        # Check if safe has transactions
        if safe.vouchers.count() > 0:
            error_msg = 'لا يمكن حذف خزينة لها معاملات مالية'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('treasury.safes_index'))
        
        # Check if balance is not zero
        if safe.balance != 0:
            error_msg = 'لا يمكن حذف خزينة بها رصيد'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 400
            flash(f'❌ {error_msg}', 'error')
            return redirect(url_for('treasury.safes_index'))
        
        safe_name = safe.name
        safe_id = safe.id
        
        db.session.delete(safe)
        db.session.commit()
        
        log_action('حذف خزينة', {'id': safe_id, 'name': safe_name})
        
        success_msg = f'تم حذف الخزينة "{safe_name}" بنجاح'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'✅ {success_msg}'
            })
        
        flash(f'✅ {success_msg}', 'success')
        return redirect(url_for('treasury.safes_index'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'خطأ في حذف الخزينة: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'❌ {error_msg}'}), 500
        
        flash(f'❌ {error_msg}', 'error')
        return redirect(url_for('treasury.safes_index'))

@bp.route('/safes/export')
def safes_export():
    """Export safes"""
    format = request.args.get('format', 'excel')
    
    safes = Safe.query.filter_by(project_id=g.project.id).order_by(Safe.name).all()
    
    if format == 'json':
        # JSON export
        data = []
        for safe in safes:
            data.append({
                'name': safe.name,
                'balance': float(safe.balance),
                'description': safe.description or '',
                'created_at': safe.created_at.isoformat() if safe.created_at else ''
            })
        
        output = io.StringIO()
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment;filename=safes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )
    
    elif format == 'csv':
        # CSV export
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['الاسم', 'الرصيد', 'الوصف', 'تاريخ الإنشاء'])
        
        # Data
        for safe in safes:
            writer.writerow([
                safe.name,
                float(safe.balance),
                safe.description or '',
                safe.created_at.strftime('%Y-%m-%d') if safe.created_at else ''
            ])
        
        output.seek(0)
        output_bytes = io.BytesIO(output.getvalue().encode('utf-8-sig'))
        
        return Response(
            output_bytes.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment;filename=safes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
    
    else:
        # Excel export (HTML table)
        return render_template('treasury/safes/export_excel.html', 
                             safes=safes,
                             datetime=datetime,
                             format_currency=format_currency)

@bp.route('/safes/report')
def safes_report():
    """Generate safes report"""
    # Get all safes
    safes = Safe.query.filter_by(project_id=g.project.id).order_by(Safe.name).all()
    
    # Calculate statistics
    total_safes = len(safes)
    total_balance = sum(s.balance for s in safes)
    
    # Get transaction summary for each safe
    safe_stats = []
    for safe in safes:
        receipts = db.session.query(func.sum(Voucher.amount)).filter_by(
            safe_id=safe.id, type='receipt'
        ).scalar() or 0
        
        payments = db.session.query(func.sum(Voucher.amount)).filter_by(
            safe_id=safe.id, type='payment'
        ).scalar() or 0
        
        safe_stats.append({
            'safe': safe,
            'receipts': receipts,
            'payments': payments
        })
    
    return render_template('treasury/safes/report.html',
                         safe_stats=safe_stats,
                         total_safes=total_safes,
                         total_balance=total_balance,
                         format_currency=format_currency)