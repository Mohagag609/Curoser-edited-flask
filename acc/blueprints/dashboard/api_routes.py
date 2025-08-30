"""
Dashboard API Routes
للتحديثات الحية والـ AJAX
"""
from flask import jsonify
from datetime import datetime, timedelta
from sqlalchemy import func
from acc.blueprints.dashboard import bp
from acc.extensions import db
from acc.models import Unit, Contract, Voucher, Customer
from acc.services.project_selection import project_required, get_current_project
from acc.services.cache_service import cached

@bp.route('/api/stats')
@project_required
def api_stats():
    """إحصائيات لوحة التحكم - JSON"""
    current_project = get_current_project()
    
    # استخدام cached function
    stats = get_dashboard_stats(current_project.id)
    
    # إضافة trend data للمخططات
    stats['sales_trend'] = get_sales_trend(current_project.id)
    
    return jsonify(stats)

@cached(timeout=60)  # Cache لمدة دقيقة
def get_dashboard_stats(project_id):
    """جلب إحصائيات لوحة التحكم مع cache"""
    stats = {}
    
    # عقود
    contract_stats = db.session.query(
        func.count(Contract.id).label('total'),
        func.sum(Contract.total_price).label('total_value')
    ).filter_by(project_id=project_id).first()
    
    stats['contracts'] = {
        'total': contract_stats.total or 0,
        'total_value': float(contract_stats.total_value or 0)
    }
    
    # وحدات
    units_by_status = db.session.query(
        Unit.status,
        func.count(Unit.id).label('count')
    ).filter_by(project_id=project_id).group_by(Unit.status).all()
    
    stats['units'] = {
        'total': sum(u.count for u in units_by_status),
        'by_status': {u.status: u.count for u in units_by_status}
    }
    
    # مالية
    finance_stats = db.session.query(
        Voucher.type,
        func.sum(Voucher.amount).label('total')
    ).filter_by(project_id=project_id).group_by(Voucher.type).all()
    
    stats['finance'] = {
        'income': next((float(f.total) for f in finance_stats if f.type == 'قبض'), 0),
        'expense': next((float(f.total) for f in finance_stats if f.type == 'صرف'), 0)
    }
    
    # عملاء
    stats['customers'] = db.session.query(func.count(Customer.id)).scalar() or 0
    
    return stats

@cached(timeout=300)  # Cache لمدة 5 دقائق
def get_sales_trend(project_id):
    """trend المبيعات لآخر 7 أيام"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    
    # جلب المبيعات لآخر 7 أيام
    sales_data = db.session.query(
        func.date(Contract.start_date).label('date'),
        func.sum(Contract.total_price).label('total')
    ).filter(
        Contract.project_id == project_id,
        Contract.start_date >= start_date
    ).group_by(
        func.date(Contract.start_date)
    ).all()
    
    # تحضير البيانات للمخطط
    sales_dict = {s.date: float(s.total) for s in sales_data}
    
    labels = []
    values = []
    
    for i in range(7):
        date = start_date + timedelta(days=i)
        labels.append(date.strftime('%d/%m'))
        values.append(sales_dict.get(date, 0))
    
    return {
        'labels': labels,
        'values': values
    }

@bp.route('/api/notifications')
@project_required
def api_notifications():
    """الإشعارات الحية"""
    current_project = get_current_project()
    
    notifications = []
    
    # أقساط متأخرة
    from acc.models import Installment
    overdue_count = Installment.query.join(Contract).filter(
        Contract.project_id == current_project.id,
        Installment.due_date < datetime.now().date(),
        Installment.status == 'مستحق'
    ).count()
    
    if overdue_count > 0:
        notifications.append({
            'type': 'warning',
            'title': 'أقساط متأخرة',
            'message': f'يوجد {overdue_count} قسط متأخر',
            'link': '/installments?status=overdue'
        })
    
    # عقود تنتهي قريباً
    expiring_contracts = Contract.query.filter(
        Contract.project_id == current_project.id,
        Contract.end_date <= datetime.now().date() + timedelta(days=30),
        Contract.status == 'نشط'
    ).count()
    
    if expiring_contracts > 0:
        notifications.append({
            'type': 'info',
            'title': 'عقود تنتهي قريباً',
            'message': f'{expiring_contracts} عقد سينتهي خلال 30 يوم',
            'link': '/contracts?expiring=true'
        })
    
    return jsonify({
        'count': len(notifications),
        'notifications': notifications
    })