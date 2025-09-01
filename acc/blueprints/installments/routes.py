from flask import render_template, request, redirect, url_for, flash, jsonify, g
from acc.blueprints.installments import bp
from acc.extensions import db
from acc.models import Installment, Contract, Unit, Customer, Voucher, Safe
from acc.services.utils import generate_uid, log_action, Pagination, format_currency, format_date
from sqlalchemy import or_, and_, func
from decimal import Decimal
from datetime import datetime, date, timedelta

@bp.route('/')
def index():
    """عرض قائمة الأقساط"""
    # Clean up any failed transactions
    try:
        db.session.rollback()
    except:
        pass
    
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    unit_id = request.args.get('unit_id', '')
    
    # البحث والتصفية
    query = Installment.query.filter_by(project_id=g.project.id)
    
    if q:
        search_term = f'%{q}%'
        query = query.outerjoin(Customer).outerjoin(Unit).filter(
            or_(
                Customer.name.ilike(search_term),
                Unit.name.ilike(search_term),
                Unit.code.ilike(search_term)
            )
        )
    
    if status:
        query = query.filter(Installment.status == status)
    
    if unit_id:
        query = query.filter(Installment.unit_id == unit_id)
    
    # الترتيب والترقيم
    query = query.order_by(Installment.due_date)
    pagination = Pagination(query, page, per_page=30)
    
    # الإحصائيات
    base_query = Installment.query.filter_by(project_id=g.project.id)
    stats = {
        'total': base_query.count(),
        'paid': base_query.filter_by(status='مدفوع').count(),
        'due': base_query.filter_by(status='مستحق').count(),
        'overdue': base_query.filter(
            and_(
                Installment.status == 'مستحق',
                Installment.due_date < date.today()
            )
        ).count(),
        'total_amount': db.session.query(func.sum(Installment.amount)).filter_by(
            project_id=g.project.id
        ).scalar() or 0,
        'paid_amount': db.session.query(func.sum(Voucher.amount)).join(
            Installment, Voucher.installment_id == Installment.id
        ).filter(
            Installment.project_id == g.project.id
        ).scalar() or 0
    }
    
    # جلب الوحدات للفلتر
    units = Unit.query.filter_by(project_id=g.project.id).order_by(Unit.code).all()
    
    return render_template('installments/index.html',
                         installments=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status,
                         unit_id=unit_id,
                         units=units,
                         stats=stats,
                         today=date.today())

@bp.route('/pro')
def index_pro():
    """نسخة محسّنة ببحث حي HTMX"""
    try:
        db.session.rollback()
    except:
        pass

    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    unit_id = request.args.get('unit_id', '')

    query = Installment.query.filter_by(project_id=g.project.id)

    if q:
        search_term = f'%{q}%'
        query = query.outerjoin(Customer).outerjoin(Unit).filter(
            or_(
                Customer.name.ilike(search_term),
                Unit.name.ilike(search_term),
                Unit.code.ilike(search_term)
            )
        )

    if status:
        query = query.filter(Installment.status == status)

    if unit_id:
        query = query.filter(Installment.unit_id == unit_id)

    query = query.order_by(Installment.due_date)
    pagination = Pagination(query, page, per_page=30)

    # الإحصائيات
    base_query = Installment.query.filter_by(project_id=g.project.id)
    stats = {
        'total': base_query.count(),
        'paid': base_query.filter_by(status='مدفوع').count(),
        'due': base_query.filter_by(status='مستحق').count(),
        'overdue': base_query.filter(
            and_(
                Installment.status == 'مستحق',
                Installment.due_date < date.today()
            )
        ).count(),
        'total_amount': db.session.query(func.sum(Installment.amount)).filter_by(
            project_id=g.project.id
        ).scalar() or 0,
        'paid_amount': db.session.query(func.sum(Voucher.amount)).join(
            Installment, Voucher.installment_id == Installment.id
        ).filter(
            Installment.project_id == g.project.id
        ).scalar() or 0
    }

    units = Unit.query.filter_by(project_id=g.project.id).order_by(Unit.code).all()

    return render_template('installments/index_pro.html',
                         installments=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status,
                         unit_id=unit_id,
                         units=units,
                         stats=stats,
                         today=date.today())

@bp.route('/table')
def table_partial():
    """Partial HTML for installments table + pagination (HTMX)."""
    try:
        db.session.rollback()
    except:
        pass

    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    status = request.args.get('status', '')
    unit_id = request.args.get('unit_id', '')

    query = Installment.query.filter_by(project_id=g.project.id)

    if q:
        search_term = f'%{q}%'
        query = query.outerjoin(Customer).outerjoin(Unit).filter(
            or_(
                Customer.name.ilike(search_term),
                Unit.name.ilike(search_term),
                Unit.code.ilike(search_term)
            )
        )

    if status:
        query = query.filter(Installment.status == status)

    if unit_id:
        query = query.filter(Installment.unit_id == unit_id)

    query = query.order_by(Installment.due_date)
    pagination = Pagination(query, page, per_page=30)

    return render_template('installments/_table.html',
                         installments=pagination.items,
                         pagination=pagination,
                         q=q,
                         status=status,
                         unit_id=unit_id,
                         today=date.today())

@bp.route('/<string:id>')
def detail(id):
    """عرض تفاصيل القسط"""
    installment = Installment.query.get_or_404(id)
    
    if installment.project_id != g.project.id:
        flash('القسط غير موجود', 'error')
        return redirect(url_for('installments.index'))
    
    # جلب السندات المرتبطة
    vouchers = Voucher.query.filter_by(installment_id=id).order_by(Voucher.date.desc()).all()
    
    # حساب المدفوع والمتبقي
    paid_amount = sum(v.amount for v in vouchers)
    remaining_amount = installment.amount - paid_amount
    
    return render_template('installments/detail.html',
                         installment=installment,
                         vouchers=vouchers,
                         paid_amount=paid_amount,
                         remaining_amount=remaining_amount,
                         date=date)

@bp.route('/<string:id>/pay', methods=['GET', 'POST'])
def pay(id):
    """دفع القسط"""
    installment = Installment.query.get_or_404(id)
    
    if installment.project_id != g.project.id:
        flash('القسط غير موجود', 'error')
        return redirect(url_for('installments.index'))
    
    if request.method == 'POST':
        try:
            amount = Decimal(request.form.get('amount', 0))
            safe_id = request.form.get('safe_id')
            payment_method = request.form.get('payment_method', 'cash')
            notes = request.form.get('notes', '')
            
            # التحقق من المبلغ
            paid_amount = installment.get_paid_amount()
            remaining = installment.amount - paid_amount
            
            if amount <= 0:
                raise Exception('المبلغ يجب أن يكون أكبر من صفر')
            
            if amount > remaining:
                raise Exception(f'المبلغ المدفوع أكبر من المتبقي ({remaining} ج.م)')
            
            # إنشاء سند القبض
            voucher = Voucher(
                id=generate_uid('VOU'),
                project_id=g.project.id,
                type='قبض',
                installment_id=id,
                customer_id=installment.customer_id,
                unit_id=installment.unit_id,
                safe_id=safe_id,
                amount=amount,
                payment_method=payment_method,
                date=date.today(),
                notes=notes
            )
            
            db.session.add(voucher)
            
            # تحديث حالة القسط
            new_paid = paid_amount + amount
            if new_paid >= installment.amount:
                installment.status = 'مدفوع'
                installment.paid_date = date.today()
            
            # تحديث رصيد الخزنة
            if safe_id:
                safe = Safe.query.get(safe_id)
                if safe:
                    safe.balance += amount
            
            db.session.commit()
            
            log_action('دفع قسط', {
                'installment_id': id,
                'amount': float(amount),
                'voucher_id': voucher.id
            })
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'تم دفع القسط بنجاح',
                    'voucher_id': voucher.id
                })
            
            flash('تم دفع القسط بنجاح', 'success')
            return redirect(url_for('installments.detail', id=id))
            
        except Exception as e:
            db.session.rollback()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)}), 400
            flash(f'خطأ: {str(e)}', 'error')
    
    # عرض نموذج الدفع
    safes = Safe.query.filter_by(project_id=g.project.id, status='نشط').all()
    paid_amount = installment.get_paid_amount()
    remaining_amount = installment.amount - paid_amount
    
    return render_template('installments/pay.html',
                         installment=installment,
                         safes=safes,
                         paid_amount=paid_amount,
                         remaining_amount=remaining_amount)

@bp.route('/upcoming')
def upcoming():
    """عرض الأقساط القادمة"""
    # الأقساط المستحقة خلال الشهر القادم
    today = date.today()
    next_month = today + timedelta(days=30)
    
    query = Installment.query.filter(
        and_(
            Installment.project_id == g.project.id,
            Installment.status == 'مستحق',
            Installment.due_date >= today,
            Installment.due_date <= next_month
        )
    ).order_by(Installment.due_date)
    
    installments = query.all()
    
    # حساب الإجمالي
    total_amount = sum(i.amount for i in installments)
    
    return render_template('installments/upcoming.html',
                         installments=installments,
                         total_amount=total_amount,
                         date_from=today,
                         date_to=next_month)

@bp.route('/overdue')
def overdue():
    """عرض الأقساط المتأخرة"""
    query = Installment.query.filter(
        and_(
            Installment.project_id == g.project.id,
            Installment.status == 'مستحق',
            Installment.due_date < date.today()
        )
    ).order_by(Installment.due_date)
    
    installments = query.all()
    
    # حساب الإجمالي والتأخير
    total_amount = 0
    for installment in installments:
        installment.days_overdue = (date.today() - installment.due_date).days
        total_amount += installment.amount - installment.get_paid_amount()
    
    return render_template('installments/overdue.html',
                         installments=installments,
                         total_amount=total_amount)

@bp.route('/search')
def search():
    """البحث في الأقساط (AJAX)"""
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    query = Installment.query.filter_by(project_id=g.project.id)
    
    if q:
        search_term = f'%{q}%'
        query = query.outerjoin(Customer).outerjoin(Unit).filter(
            or_(
                Customer.name.ilike(search_term),
                Unit.name.ilike(search_term),
                Unit.code.ilike(search_term)
            )
        )
    
    query = query.order_by(Installment.due_date)
    pagination = Pagination(query, page, per_page=30)
    
    installments = []
    for installment in pagination.items:
        installments.append({
            'id': installment.id,
            'customer_name': installment.customer.name if installment.customer else '',
            'unit_name': installment.unit.name if installment.unit else '',
            'unit_code': installment.unit.code if installment.unit else '',
            'amount': float(installment.amount),
            'paid_amount': float(installment.get_paid_amount()),
            'due_date': installment.due_date.strftime('%Y-%m-%d'),
            'status': installment.status,
            'installment_number': installment.installment_number
        })
    
    return jsonify({
        'success': True,
        'installments': installments,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'total': pagination.total,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    })