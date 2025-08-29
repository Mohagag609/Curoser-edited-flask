from flask import render_template, request, redirect, url_for, flash, jsonify, Response
from acc.blueprints.treasury import bp
from acc.models import Safe, SafeTransfer, Voucher
from acc.extensions import db
from acc.services.utils import generate_uid, log_action, Pagination, parse_number, get_today, format_currency
from acc.services.project_context import get_current_project, filter_by_project
from acc.services.code_generator import generate_safe_code
from datetime import datetime
from sqlalchemy import func
import io
import csv
import json

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    
    # Get all safes for current project
    safes = filter_by_project(Safe.query, Safe).order_by(Safe.is_default.desc(), Safe.name).all()
    
    # Update balances
    for safe in safes:
        safe.update_balance()
    db.session.commit()
    
    # Calculate totals for current project
    safe_query = filter_by_project(db.session.query(func.sum(Safe.balance)), Safe)
    total_cash = safe_query.filter(Safe.type == 'cash').scalar() or 0
    total_bank = safe_query.filter(Safe.type == 'bank').scalar() or 0
    total_balance = total_cash + total_bank
    
    # Get recent transfers
    recent_transfers = SafeTransfer.query.order_by(SafeTransfer.date.desc()).limit(10).all()
    
    return render_template('treasury/index.html',
                         safes=safes,
                         total_cash=total_cash,
                         total_bank=total_bank,
                         total_balance=total_balance,
                         recent_transfers=recent_transfers)


@bp.route('/safes/add', methods=['GET', 'POST'])
def add_safe():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        safe_type = request.form.get('type', 'cash')
        bank_name = request.form.get('bank_name', '').strip()
        account_number = request.form.get('account_number', '').strip()
        is_default = request.form.get('is_default') == '1'
        notes = request.form.get('notes', '').strip()
        
        if not name:
            flash('الرجاء إدخال اسم الخزينة', 'error')
            return redirect(url_for('treasury.add_safe'))
        
        # Check duplicate
        if Safe.query.filter_by(name=name).first():
            flash('اسم الخزينة موجود بالفعل', 'error')
            return redirect(url_for('treasury.add_safe'))
        
        # Get current project
        current_project = get_current_project()
        if not current_project:
            flash('الرجاء اختيار مشروع أولاً', 'error')
            return redirect(url_for('projects.index'))
        
        # If setting as default, unset other defaults in current project
        if is_default:
            filter_by_project(Safe.query, Safe).update({'is_default': False})
        
        safe = Safe(
            id=generate_uid('SF'),
            project_id=current_project.id,
            code=generate_safe_code(),
            name=name,
            type=safe_type,
            bank_name=bank_name if safe_type == 'bank' else None,
            account_number=account_number if safe_type == 'bank' else None,
            is_default=is_default,
            notes=notes
        )
        
        try:
            db.session.add(safe)
            log_action('إضافة خزينة جديدة', {'id': safe.id, 'name': safe.name})
            db.session.commit()
            
            flash(f'✅ تم إضافة الخزينة بنجاح! رقم الخزينة: {safe.code}', 'success')
            
            # Handle AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'تم إضافة الخزينة بنجاح! رقم الخزينة: {safe.code}',
                    'redirect': url_for('treasury.safe_detail', id=safe.id)
                })
                
            return redirect(url_for('treasury.safe_detail', id=safe.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'❌ حدث خطأ أثناء إضافة الخزينة: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg}), 500
                
            flash(error_msg, 'error')
            return redirect(url_for('treasury.add_safe'))
    
    return render_template('treasury/add_safe.html')


@bp.route('/safes/<id>')
def safe_detail(id):
    safe = Safe.query.get_or_404(id)
    
    # Update balance
    safe.update_balance()
    db.session.commit()
    
    # Get vouchers
    page = request.args.get('page', 1, type=int)
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    voucher_type = request.args.get('type', '')
    
    query = Voucher.query.filter_by(safe_id=id)
    
    if from_date:
        query = query.filter(Voucher.date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    
    if to_date:
        query = query.filter(Voucher.date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    
    if voucher_type:
        query = query.filter(Voucher.type == voucher_type)
    
    query = query.order_by(Voucher.date.desc(), Voucher.created_at.desc())
    
    pagination = Pagination(query, page)
    vouchers = pagination.items
    
    # Get transfers
    transfers_out = SafeTransfer.query.filter_by(from_safe_id=id).order_by(SafeTransfer.date.desc()).limit(5).all()
    transfers_in = SafeTransfer.query.filter_by(to_safe_id=id).order_by(SafeTransfer.date.desc()).limit(5).all()
    
    return render_template('treasury/safe_detail.html',
                         safe=safe,
                         vouchers=vouchers,
                         pagination=pagination,
                         from_date=from_date,
                         to_date=to_date,
                         voucher_type=voucher_type,
                         transfers_out=transfers_out,
                         transfers_in=transfers_in)


@bp.route('/safes/<id>/edit', methods=['GET', 'POST'])
def edit_safe(id):
    safe = Safe.query.get_or_404(id)
    
    if request.method == 'POST':
        safe.name = request.form.get('name', '').strip()
        safe.type = request.form.get('type', 'cash')
        safe.bank_name = request.form.get('bank_name', '').strip() if safe.type == 'bank' else None
        safe.account_number = request.form.get('account_number', '').strip() if safe.type == 'bank' else None
        safe.is_default = request.form.get('is_default') == '1'
        safe.notes = request.form.get('notes', '').strip()
        
        if not safe.name:
            flash('الرجاء إدخال اسم الخزينة', 'error')
            return redirect(url_for('treasury.edit_safe', id=id))
        
        # Check duplicate
        existing = Safe.query.filter_by(name=safe.name).first()
        if existing and existing.id != id:
            flash('اسم الخزينة موجود بالفعل', 'error')
            return redirect(url_for('treasury.edit_safe', id=id))
        
        # If setting as default, unset other defaults
        if safe.is_default:
            Safe.query.filter(Safe.id != id).update({'is_default': False})
        
        log_action('تعديل خزينة', {'id': safe.id, 'name': safe.name})
        db.session.commit()
        
        flash('تم تحديث بيانات الخزينة بنجاح', 'success')
        return redirect(url_for('treasury.safe_detail', id=id))
    
    return render_template('treasury/edit_safe.html', safe=safe)


@bp.route('/transfers')
def transfers():
    page = request.args.get('page', 1, type=int)
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    
    query = SafeTransfer.query
    
    if from_date:
        query = query.filter(SafeTransfer.date >= datetime.strptime(from_date, '%Y-%m-%d'))
    
    if to_date:
        query = query.filter(SafeTransfer.date <= datetime.strptime(to_date, '%Y-%m-%d'))
    
    query = query.order_by(SafeTransfer.date.desc())
    
    pagination = Pagination(query, page)
    transfers = pagination.items
    
    return render_template('treasury/transfers.html',
                         transfers=transfers,
                         pagination=pagination,
                         from_date=from_date,
                         to_date=to_date)


@bp.route('/transfers/add', methods=['GET', 'POST'])
def add_transfer():
    if request.method == 'POST':
        from_safe_id = request.form.get('from_safe_id')
        to_safe_id = request.form.get('to_safe_id')
        amount = parse_number(request.form.get('amount', 0))
        date = request.form.get('date', get_today().isoformat())
        description = request.form.get('description', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not all([from_safe_id, to_safe_id, amount]):
            flash('الرجاء إدخال جميع البيانات المطلوبة', 'error')
            return redirect(url_for('treasury.add_transfer'))
        
        if from_safe_id == to_safe_id:
            flash('لا يمكن التحويل من وإلى نفس الخزينة', 'error')
            return redirect(url_for('treasury.add_transfer'))
        
        if amount <= 0:
            flash('الرجاء إدخال مبلغ صحيح', 'error')
            return redirect(url_for('treasury.add_transfer'))
        
        # Check source safe balance
        from_safe = Safe.query.get(from_safe_id)
        from_safe.update_balance()
        
        if from_safe.balance < amount:
            flash(f'الرصيد غير كافي في {from_safe.name}. الرصيد المتاح: {from_safe.balance}', 'error')
            return redirect(url_for('treasury.add_transfer'))
        
        transfer = SafeTransfer(
            from_safe_id=from_safe_id,
            to_safe_id=to_safe_id,
            amount=amount,
            date=datetime.strptime(date, '%Y-%m-%d') if isinstance(date, str) else date,
            description=description,
            notes=notes
        )
        
        db.session.add(transfer)
        
        # Update safe balances
        from_safe.update_balance()
        to_safe = Safe.query.get(to_safe_id)
        to_safe.update_balance()
        
        log_action('تحويل بين الخزائن', {
            'id': transfer.id,
            'from_safe': from_safe.name,
            'to_safe': to_safe.name,
            'amount': amount
        })
        
        db.session.commit()
        
        flash('تم إجراء التحويل بنجاح', 'success')
        return redirect(url_for('treasury.transfers'))
    
    safes = Safe.query.order_by(Safe.name).all()
    return render_template('treasury/add_transfer.html',
                         safes=safes,
                         today=get_today())


@bp.route('/transfers/<id>/delete', methods=['POST'])
def delete_transfer(id):
    transfer = SafeTransfer.query.get_or_404(id)
    
    # Update safe balances
    from_safe = transfer.from_safe
    to_safe = transfer.to_safe
    
    db.session.delete(transfer)
    
    from_safe.update_balance()
    to_safe.update_balance()
    
    log_action('حذف تحويل', {
        'id': id,
        'from_safe': from_safe.name,
        'to_safe': to_safe.name,
        'amount': transfer.amount
    })
    
    db.session.commit()
    
    flash('تم حذف التحويل بنجاح', 'success')
    return redirect(request.referrer or url_for('treasury.transfers'))


# API endpoints
@bp.route('/api/safes')
def api_safes():
    safes = filter_by_project(Safe.query, Safe).order_by(Safe.is_default.desc(), Safe.name).all()
    for safe in safes:
        safe.update_balance()
    
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'type': s.type,
        'balance': float(s.balance),
        'is_default': s.is_default
    } for s in safes])


@bp.route('/export/<format>')
def export(format):
    """تصدير بيانات الخزائن"""
    safes = filter_by_project(Safe.query, Safe).order_by(Safe.name).all()
    
    # Update balances
    for safe in safes:
        safe.update_balance()
    
    if format == 'excel':
        output = io.StringIO()
        output.write('<html><head><meta charset="utf-8"></head><body>')
        output.write('<table border="1">')
        output.write('<tr>')
        output.write('<th>رقم الخزينة</th>')
        output.write('<th>اسم الخزينة</th>')
        output.write('<th>النوع</th>')
        output.write('<th>البنك</th>')
        output.write('<th>رقم الحساب</th>')
        output.write('<th>الرصيد</th>')
        output.write('<th>خزينة افتراضية</th>')
        output.write('</tr>')
        
        for safe in safes:
            output.write('<tr>')
            output.write(f'<td>{safe.code}</td>')
            output.write(f'<td>{safe.name}</td>')
            output.write(f'<td>{"نقدي" if safe.type == "cash" else "بنكي"}</td>')
            output.write(f'<td>{safe.bank_name or ""}</td>')
            output.write(f'<td>{safe.account_number or ""}</td>')
            output.write(f'<td>{format_currency(safe.balance)}</td>')
            output.write(f'<td>{"نعم" if safe.is_default else "لا"}</td>')
            output.write('</tr>')
        
        output.write('</table></body></html>')
        
        response = Response(output.getvalue(), content_type='application/vnd.ms-excel')
        response.headers['Content-Disposition'] = f'attachment; filename=safes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
        return response
    
    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['رقم الخزينة', 'اسم الخزينة', 'النوع', 'البنك', 'رقم الحساب', 'الرصيد', 'خزينة افتراضية'])
        
        for safe in safes:
            writer.writerow([
                safe.code,
                safe.name,
                'نقدي' if safe.type == 'cash' else 'بنكي',
                safe.bank_name or '',
                safe.account_number or '',
                safe.balance,
                'نعم' if safe.is_default else 'لا'
            ])
        
        output.seek(0)
        response = Response(output.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response.headers['Content-Disposition'] = f'attachment; filename=safes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return response
    
    elif format == 'json':
        data = []
        for safe in safes:
            data.append({
                'code': safe.code,
                'name': safe.name,
                'type': safe.type,
                'bank_name': safe.bank_name,
                'account_number': safe.account_number,
                'balance': float(safe.balance),
                'is_default': safe.is_default
            })
        
        return jsonify(data)
    
    return redirect(url_for('treasury.index'))


@bp.route('/report')
def report():
    """صفحة التقارير"""
    current_project = get_current_project()
    
    # إحصائيات عامة
    safes = filter_by_project(Safe.query, Safe).all()
    for safe in safes:
        safe.update_balance()
    
    total_safes = len(safes)
    cash_safes = [s for s in safes if s.type == 'cash']
    bank_safes = [s for s in safes if s.type == 'bank']
    
    total_cash = sum(s.balance for s in cash_safes)
    total_bank = sum(s.balance for s in bank_safes)
    total_balance = total_cash + total_bank
    
    # الحركات الأخيرة
    recent_transfers = SafeTransfer.query.order_by(SafeTransfer.date.desc()).limit(10).all()
    
    # إحصائيات الحركات
    transfers_count = SafeTransfer.query.count()
    transfers_total = db.session.query(func.sum(SafeTransfer.amount)).scalar() or 0
    
    return render_template('treasury/report.html',
                         total_safes=total_safes,
                         cash_safes=len(cash_safes),
                         bank_safes=len(bank_safes),
                         total_cash=total_cash,
                         total_bank=total_bank,
                         total_balance=total_balance,
                         recent_transfers=recent_transfers,
                         transfers_count=transfers_count,
                         transfers_total=transfers_total,
                         safes=safes,
                         format_currency=format_currency)