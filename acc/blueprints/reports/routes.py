from flask import render_template, request, Response
from acc.blueprints.reports import bp
from acc.models import (Unit, Customer, Contract, Installment, Voucher, Safe, Partner, Broker,
                       Project, Phase, Expense, MaterialIssue, PartnerLedger, PhaseSettlement,
                       PhaseSettlementLine, ProjectPartner)
from acc.extensions import db
from acc.services.utils import get_today, format_currency
from acc.services.project_context import get_current_project
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import csv
import io

@bp.route('/')
def index():
    return render_template('reports/index.html')


@bp.route('/units-status')
def units_status():
    # Get units grouped by status
    units_by_status = db.session.query(
        Unit.status,
        func.count(Unit.id).label('count'),
        func.sum(Unit.total_price).label('total_value')
    ).group_by(Unit.status).all()
    
    # Get all units with details
    units = Unit.query.order_by(Unit.status, Unit.code).all()
    
    # Calculate totals
    total_units = sum(item.count for item in units_by_status)
    total_value = sum(item.total_value or 0 for item in units_by_status)
    
    return render_template('reports/units_status.html',
                         units_by_status=units_by_status,
                         units=units,
                         total_units=total_units,
                         total_value=total_value)


@bp.route('/installments-schedule')
def installments_schedule():
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    status = request.args.get('status', '')
    
    # Base query
    query = Installment.query
    
    # Apply filters
    if from_date:
        query = query.filter(Installment.due_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    
    if to_date:
        query = query.filter(Installment.due_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    
    if status:
        query = query.filter(Installment.status == status)
    
    # Get installments with unit and contract info
    installments = query.join(Unit).order_by(Installment.due_date).all()
    
    # Calculate summary
    total_count = len(installments)
    total_amount = sum(i.original_amount or 0 for i in installments)
    paid_amount = sum((i.original_amount or 0) - (i.amount or 0) for i in installments)
    remaining_amount = sum(i.amount or 0 for i in installments)
    
    # Group by month
    monthly_summary = {}
    for installment in installments:
        month_key = installment.due_date.strftime('%Y-%m')
        if month_key not in monthly_summary:
            monthly_summary[month_key] = {
                'count': 0,
                'amount': 0,
                'paid': 0,
                'remaining': 0
            }
        monthly_summary[month_key]['count'] += 1
        monthly_summary[month_key]['amount'] += installment.original_amount or 0
        monthly_summary[month_key]['paid'] += (installment.original_amount or 0) - (installment.amount or 0)
        monthly_summary[month_key]['remaining'] += installment.amount or 0
    
    return render_template('reports/installments_schedule.html',
                         installments=installments,
                         from_date=from_date,
                         to_date=to_date,
                         status=status,
                         total_count=total_count,
                         total_amount=total_amount,
                         paid_amount=paid_amount,
                         remaining_amount=remaining_amount,
                         monthly_summary=monthly_summary)


@bp.route('/financial-summary')
def financial_summary():
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    
    # Date filter for vouchers
    voucher_query = Voucher.query
    if from_date:
        voucher_query = voucher_query.filter(Voucher.date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        voucher_query = voucher_query.filter(Voucher.date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    
    # Calculate totals
    total_receipts = voucher_query.filter_by(type='receipt').with_entities(func.sum(Voucher.amount)).scalar() or 0
    total_payments = voucher_query.filter_by(type='payment').with_entities(func.sum(Voucher.amount)).scalar() or 0
    net_income = total_receipts - total_payments
    
    # Get vouchers by safe
    vouchers_by_safe = db.session.query(
        Safe.name,
        Voucher.type,
        func.sum(Voucher.amount).label('total')
    ).join(Safe).filter(
        Voucher.safe_id == Safe.id
    )
    
    if from_date:
        vouchers_by_safe = vouchers_by_safe.filter(Voucher.date >= datetime.strptime(from_date, '%Y-%m-%d').date())
    if to_date:
        vouchers_by_safe = vouchers_by_safe.filter(Voucher.date <= datetime.strptime(to_date, '%Y-%m-%d').date())
    
    vouchers_by_safe = vouchers_by_safe.group_by(Safe.name, Voucher.type).all()
    
    # Get recent vouchers
    recent_vouchers = voucher_query.order_by(Voucher.date.desc(), Voucher.created_at.desc()).limit(20).all()
    
    # Get safe balances
    safes = Safe.query.all()
    for safe in safes:
        safe.update_balance()
    
    total_balance = sum(safe.balance for safe in safes)
    
    return render_template('reports/financial_summary.html',
                         from_date=from_date,
                         to_date=to_date,
                         total_receipts=total_receipts,
                         total_payments=total_payments,
                         net_income=net_income,
                         vouchers_by_safe=vouchers_by_safe,
                         recent_vouchers=recent_vouchers,
                         safes=safes,
                         total_balance=total_balance)


@bp.route('/customers-balance')
def customers_balance():
    # Get all customers with their contract totals
    customers_data = []
    
    customers = Customer.query.order_by(Customer.name).all()
    for customer in customers:
        contracts = Contract.query.filter_by(customer_id=customer.id).all()
        
        total_contracts = len(contracts)
        total_value = sum((c.total_price or 0) - (c.discount_amount or 0) for c in contracts)
        
        # Calculate paid amount from vouchers
        paid_amount = 0
        for contract in contracts:
            # Direct contract payments
            contract_payments = db.session.query(func.sum(Voucher.amount)).filter(
                Voucher.type == 'receipt',
                Voucher.linked_type == 'contract',
                Voucher.linked_ref == contract.id
            ).scalar() or 0
            
            # Installment payments
            installment_ids = [i.id for i in contract.installments]
            if installment_ids:
                installment_payments = db.session.query(func.sum(Voucher.amount)).filter(
                    Voucher.type == 'receipt',
                    Voucher.linked_type == 'installment',
                    Voucher.linked_ref.in_(installment_ids)
                ).scalar() or 0
            else:
                installment_payments = 0
            
            paid_amount += contract_payments + installment_payments
        
        remaining = total_value - paid_amount
        
        if total_contracts > 0:  # Only include customers with contracts
            customers_data.append({
                'customer': customer,
                'total_contracts': total_contracts,
                'total_value': total_value,
                'paid_amount': paid_amount,
                'remaining': remaining,
                'percentage': (paid_amount / total_value * 100) if total_value > 0 else 0
            })
    
    # Sort by remaining amount descending
    customers_data.sort(key=lambda x: x['remaining'], reverse=True)
    
    # Calculate totals
    total_value = sum(c['total_value'] for c in customers_data)
    total_paid = sum(c['paid_amount'] for c in customers_data)
    total_remaining = sum(c['remaining'] for c in customers_data)
    
    return render_template('reports/customers_balance.html',
                         customers_data=customers_data,
                         total_value=total_value,
                         total_paid=total_paid,
                         total_remaining=total_remaining)


@bp.route('/partners-summary')
def partners_summary():
    # Get all partners with their units and percentages
    partners_data = []
    
    partners = Partner.query.order_by(Partner.name).all()
    for partner in partners:
        unit_partners = partner.unit_partners.all()
        
        units_count = len(unit_partners)
        total_value = 0
        units_details = []
        
        for up in unit_partners:
            unit_value = (up.unit.total_price or 0) * up.percentage / 100
            total_value += unit_value
            units_details.append({
                'unit': up.unit,
                'percentage': up.percentage,
                'value': unit_value
            })
        
        # Get partner debts
        debts_owed = partner.debts_owed.filter_by(status='نشط').all()
        debts_due = partner.debts_due.filter_by(status='نشط').all()
        
        total_owed = sum(debt.remaining_amount for debt in debts_owed)
        total_due = sum(debt.remaining_amount for debt in debts_due)
        
        partners_data.append({
            'partner': partner,
            'units_count': units_count,
            'total_value': total_value,
            'units_details': units_details,
            'total_owed': total_owed,
            'total_due': total_due,
            'net_balance': total_owed - total_due
        })
    
    # Sort by total value descending
    partners_data.sort(key=lambda x: x['total_value'], reverse=True)
    
    return render_template('reports/partners_summary.html',
                         partners_data=partners_data)


@bp.route('/brokers-commissions')
def brokers_commissions():
    # Get all contracts with broker info
    contracts_with_brokers = Contract.query.filter(
        Contract.broker_name.isnot(None),
        Contract.broker_amount > 0
    ).order_by(Contract.created_at.desc()).all()
    
    # Group by broker
    brokers_data = {}
    for contract in contracts_with_brokers:
        broker_name = contract.broker_name
        if broker_name not in brokers_data:
            brokers_data[broker_name] = {
                'name': broker_name,
                'contracts_count': 0,
                'total_sales': 0,
                'total_commission': 0,
                'contracts': []
            }
        
        brokers_data[broker_name]['contracts_count'] += 1
        brokers_data[broker_name]['total_sales'] += contract.total_price or 0
        brokers_data[broker_name]['total_commission'] += contract.broker_amount or 0
        brokers_data[broker_name]['contracts'].append(contract)
    
    # Convert to list and sort
    brokers_list = list(brokers_data.values())
    brokers_list.sort(key=lambda x: x['total_commission'], reverse=True)
    
    # Calculate totals
    total_contracts = len(contracts_with_brokers)
    total_sales = sum(b['total_sales'] for b in brokers_list)
    total_commissions = sum(b['total_commission'] for b in brokers_list)
    
    return render_template('reports/brokers_commissions.html',
                         brokers_list=brokers_list,
                         total_contracts=total_contracts,
                         total_sales=total_sales,
                         total_commissions=total_commissions)


# Export functions
@bp.route('/export/<report_type>')
def export_report(report_type):
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type == 'units-status':
        # Write headers
        writer.writerow(['كود الوحدة', 'الاسم', 'المبنى', 'الدور', 'المساحة', 'السعر', 'الحالة'])
        
        # Write data
        units = Unit.query.order_by(Unit.status, Unit.code).all()
        for unit in units:
            writer.writerow([
                unit.code,
                unit.name or '',
                unit.building or '',
                unit.floor or '',
                unit.area or '',
                unit.total_price or 0,
                unit.status
            ])
    
    elif report_type == 'customers-balance':
        # Write headers
        writer.writerow(['العميل', 'الهاتف', 'عدد العقود', 'إجمالي القيمة', 'المدفوع', 'المتبقي', 'نسبة السداد'])
        
        # Get customer data (same logic as customers_balance view)
        customers = Customer.query.order_by(Customer.name).all()
        for customer in customers:
            contracts = Contract.query.filter_by(customer_id=customer.id).all()
            if not contracts:
                continue
            
            total_contracts = len(contracts)
            total_value = sum((c.total_price or 0) - (c.discount_amount or 0) for c in contracts)
            
            # Calculate paid amount
            paid_amount = 0
            for contract in contracts:
                contract_payments = db.session.query(func.sum(Voucher.amount)).filter(
                    Voucher.type == 'receipt',
                    Voucher.linked_type == 'contract',
                    Voucher.linked_ref == contract.id
                ).scalar() or 0
                
                installment_ids = [i.id for i in contract.installments]
                if installment_ids:
                    installment_payments = db.session.query(func.sum(Voucher.amount)).filter(
                        Voucher.type == 'receipt',
                        Voucher.linked_type == 'installment',
                        Voucher.linked_ref.in_(installment_ids)
                    ).scalar() or 0
                else:
                    installment_payments = 0
                
                paid_amount += contract_payments + installment_payments
            
            remaining = total_value - paid_amount
            percentage = (paid_amount / total_value * 100) if total_value > 0 else 0
            
            writer.writerow([
                customer.name,
                customer.phone or '',
                total_contracts,
                total_value,
                paid_amount,
                remaining,
                f"{percentage:.1f}%"
            ])
    
    # Create response
    output.seek(0)
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={report_type}-{datetime.now().strftime("%Y%m%d")}.csv',
            'Content-Type': 'text/csv; charset=utf-8-sig'
        }
    )
    
    # Add BOM for Excel Arabic support
    return '\ufeff' + output.getvalue(), response.status_code, response.headers


@bp.route('/project-expenses')
def project_expenses():
    """تقرير مصروفات المشاريع"""
    project_id = request.args.get('project_id', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    
    # الاستعلام الأساسي للمشاريع
    projects = Project.query.filter_by(status='نشط').order_by(Project.name).all()
    
    # البيانات حسب المشروع المحدد أو الحالي
    selected_project = None
    phases_data = []
    total_expenses = 0
    total_materials = 0
    total_cost = 0
    
    if project_id:
        selected_project = Project.query.get(project_id)
    else:
        selected_project = get_current_project()
    
    if selected_project:
        # جلب المراحل
        phases_query = Phase.query.filter_by(project_id=selected_project.id)
        
        # فلترة التاريخ
        if from_date:
            phases_query = phases_query.filter(Phase.start_date >= datetime.strptime(from_date, '%Y-%m-%d'))
        if to_date:
            phases_query = phases_query.filter(Phase.start_date <= datetime.strptime(to_date, '%Y-%m-%d'))
        
        phases = phases_query.order_by(Phase.start_date).all()
        
        for phase in phases:
            phase_data = {
                'phase': phase,
                'expenses': phase.total_expenses(),
                'materials': phase.total_materials(),
                'total': phase.total_cost(),
                'is_settled': phase.is_settled
            }
            phases_data.append(phase_data)
            total_expenses += phase_data['expenses']
            total_materials += phase_data['materials']
            total_cost += phase_data['total']
    
    return render_template('reports/project_expenses.html',
                         projects=projects,
                         selected_project=selected_project,
                         project_id=project_id,
                         phases_data=phases_data,
                         total_expenses=total_expenses,
                         total_materials=total_materials,
                         total_cost=total_cost,
                         from_date=from_date,
                         to_date=to_date)


@bp.route('/partner-balances')
def partner_balances():
    """تقرير أرصدة الشركاء"""
    project_id = request.args.get('project_id', '')
    
    # جلب جميع المشاريع
    projects = Project.query.filter_by(status='نشط').order_by(Project.name).all()
    
    # البيانات
    ledger_data = []
    selected_project = None
    
    if project_id:
        selected_project = Project.query.get(project_id)
        ledgers = PartnerLedger.query.filter_by(project_id=project_id).all()
        
        for ledger in ledgers:
            ledger_data.append({
                'partner': ledger.partner,
                'balance': float(ledger.balance),
                'status': 'دائن' if ledger.balance < 0 else ('مدين' if ledger.balance > 0 else 'متوازن'),
                'last_updated': ledger.last_updated,
                'settlements_count': PhaseSettlement.query.join(
                    PhaseSettlementLine
                ).filter(
                    PhaseSettlementLine.partner_id == ledger.partner_id,
                    Phase.project_id == project_id
                ).count()
            })
    
    # حساب الإجماليات
    total_debit = sum(item['balance'] for item in ledger_data if item['balance'] > 0)
    total_credit = sum(abs(item['balance']) for item in ledger_data if item['balance'] < 0)
    
    # ترتيب حسب الرصيد
    ledger_data.sort(key=lambda x: x['balance'], reverse=True)
    
    return render_template('reports/partner_balances.html',
                         projects=projects,
                         selected_project=selected_project,
                         project_id=project_id,
                         ledger_data=ledger_data,
                         total_debit=total_debit,
                         total_credit=total_credit)


@bp.route('/phase-settlements')
def phase_settlements():
    """تقرير تسويات المراحل"""
    project_id = request.args.get('project_id', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    
    # الاستعلام الأساسي
    query = PhaseSettlement.query.join(Phase)
    
    # فلترة المشروع
    if project_id:
        query = query.filter(Phase.project_id == project_id)
    
    # فلترة التاريخ
    if from_date:
        query = query.filter(PhaseSettlement.settlement_date >= datetime.strptime(from_date, '%Y-%m-%d'))
    if to_date:
        query = query.filter(PhaseSettlement.settlement_date <= datetime.strptime(to_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    
    # ترتيب حسب التاريخ
    settlements = query.order_by(PhaseSettlement.settlement_date.desc()).all()
    
    # جلب المشاريع
    projects = Project.query.filter_by(status='نشط').order_by(Project.name).all()
    
    # حساب الإجماليات
    total_amount = sum(s.total_amount for s in settlements)
    total_count = len(settlements)
    
    return render_template('reports/phase_settlements.html',
                         settlements=settlements,
                         projects=projects,
                         project_id=project_id,
                         from_date=from_date,
                         to_date=to_date,
                         total_amount=total_amount,
                         total_count=total_count)


@bp.route('/project-summary')
def project_summary():
    """تقرير ملخص المشروع"""
    project_id = request.args.get('project_id', '')
    
    if not project_id:
        current_project = get_current_project()
        if current_project:
            project_id = current_project.id
    
    project = None
    summary_data = {}
    
    if project_id:
        project = Project.query.get(project_id)
        if project:
            # حساب البيانات
            summary_data = {
                'project': project,
                'units_count': project.units.count(),
                'units_available': project.units.filter_by(status='متاحة').count(),
                'units_sold': project.units.filter_by(status='مباعة').count(),
                'units_reserved': project.units.filter_by(status='محجوزة').count(),
                'contracts_count': project.contracts.count(),
                'contracts_active': project.contracts.filter_by(status='نشط').count(),
                'phases_count': Phase.query.filter_by(project_id=project_id).count(),
                'phases_settled': Phase.query.filter_by(project_id=project_id).filter(Phase.settled_at.isnot(None)).count(),
                'total_cost': project.calculate_total_cost(),
                'budget_remaining': (project.budget or 0) - project.calculate_total_cost(),
                'partners_count': ProjectPartner.query.filter_by(project_id=project_id, is_active=True).count(),
                'safes_count': project.safes.count(),
                'safes_balance': db.session.query(func.sum(Safe.balance)).filter_by(project_id=project_id).scalar() or 0
            }
    
    # جلب جميع المشاريع
    projects = Project.query.filter_by(status='نشط').order_by(Project.name).all()
    
    return render_template('reports/project_summary.html',
                         project=project,
                         projects=projects,
                         project_id=project_id,
                         summary_data=summary_data)