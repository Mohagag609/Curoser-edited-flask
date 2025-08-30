"""خدمات تسوية الشركاء بالمرحلة"""
from typing import Dict, List, Any
from decimal import Decimal
from datetime import datetime
from acc.models import (Phase, ProjectPartner, Partner, Expense, MaterialIssue, 
                       PartnerLedger, PhaseSettlement, PhaseSettlementLine)
from acc.extensions import db
from acc.services.utils import generate_uid
from sqlalchemy import func


def compute_phase_settlement(phase_id: str) -> Dict[str, Any]:
    """
    حساب تسوية المرحلة
    Returns:
        {
            'phase': Phase object,
            'total_expenses': float,
            'total_materials': float,
            'total_cost': float,
            'partners_count': int,
            'average_per_partner': float,
            'partners_data': [
                {
                    'partner': Partner object,
                    'paid_amount': float,
                    'difference': float,  # موجب = عليه، سالب = له
                    'current_balance': float
                }
            ],
            'can_settle': bool,
            'error': str or None
        }
    """
    phase = Phase.query.get(phase_id)
    if not phase:
        return {'error': 'المرحلة غير موجودة'}
    
    if phase.is_settled:
        return {'error': 'المرحلة متسوية بالفعل'}
    
    # جلب الشركاء النشطين في المشروع
    project_partners = ProjectPartner.query.filter_by(
        project_id=phase.project_id,
        is_active=True
    ).all()
    
    if not project_partners:
        return {'error': 'لا يوجد شركاء نشطين في المشروع'}
    
    partners_count = len(project_partners)
    
    # حساب إجمالي المصروفات والمواد
    total_expenses = phase.total_expenses()
    total_materials = phase.total_materials()
    total_cost = total_expenses + total_materials
    
    # حساب المتوسط لكل شريك
    average_per_partner = total_cost / partners_count if partners_count > 0 else 0
    
    # حساب البيانات لكل شريك
    partners_data = []
    
    for pp in project_partners:
        partner = Partner.query.get(pp.partner_id)
        
        # حساب ما دفعه الشريك في هذه المرحلة
        partner_expenses = db.session.query(func.sum(Expense.amount)).filter_by(
            phase_id=phase_id,
            paid_by_partner_id=partner.id
        ).scalar() or 0
        
        partner_materials = db.session.query(
            func.sum(MaterialIssue.quantity * MaterialIssue.unit_cost)
        ).filter_by(
            phase_id=phase_id,
            issued_by_partner_id=partner.id
        ).scalar() or 0
        
        paid_amount = float(partner_expenses) + float(partner_materials)
        
        # حساب الفرق (المتوسط - ما دفعه)
        # موجب = عليه دفع، سالب = له استرداد
        difference = average_per_partner - paid_amount
        
        # جلب الرصيد الحالي من دفتر الشريك
        ledger = PartnerLedger.query.filter_by(
            project_id=phase.project_id,
            partner_id=partner.id
        ).first()
        
        current_balance = float(ledger.balance) if ledger else 0
        
        partners_data.append({
            'partner': partner,
            'paid_amount': paid_amount,
            'difference': difference,
            'current_balance': current_balance,
            'new_balance': current_balance + difference
        })
    
    return {
        'phase': phase,
        'total_expenses': total_expenses,
        'total_materials': total_materials,
        'total_cost': total_cost,
        'partners_count': partners_count,
        'average_per_partner': average_per_partner,
        'partners_data': partners_data,
        'can_settle': total_cost > 0,
        'error': None
    }


def settle_phase(phase_id: str, notes: str = None, created_by: str = None) -> Dict[str, Any]:
    """
    تنفيذ تسوية المرحلة
    Returns:
        {
            'success': bool,
            'settlement': PhaseSettlement or None,
            'message': str,
            'error': str or None
        }
    """
    # حساب التسوية أولاً
    calculation = compute_phase_settlement(phase_id)
    
    if calculation.get('error'):
        return {
            'success': False,
            'settlement': None,
            'message': '',
            'error': calculation['error']
        }
    
    if not calculation.get('can_settle'):
        return {
            'success': False,
            'settlement': None,
            'message': '',
            'error': 'لا يمكن تسوية مرحلة بدون مصروفات'
        }
    
    phase = calculation['phase']
    
    try:
        # بدء transaction
        # إنشاء سجل التسوية
        settlement = PhaseSettlement(
            id=generate_uid('PSET'),
            phase_id=phase_id,
            total_expenses=calculation['total_expenses'],
            total_materials=calculation['total_materials'],
            total_amount=calculation['total_cost'],
            partners_count=calculation['partners_count'],
            average_per_partner=calculation['average_per_partner'],
            notes=notes,
            created_by=created_by
        )
        db.session.add(settlement)
        
        # إنشاء سطور التسوية وتحديث دفاتر الشركاء
        for partner_data in calculation['partners_data']:
            partner = partner_data['partner']
            
            # إنشاء سطر التسوية
            line = PhaseSettlementLine(
                id=generate_uid('PSETL'),
                settlement_id=settlement.id,
                partner_id=partner.id,
                paid_amount=partner_data['paid_amount'],
                average_amount=calculation['average_per_partner'],
                difference=partner_data['difference'],
                previous_balance=partner_data['current_balance'],
                new_balance=partner_data['new_balance']
            )
            db.session.add(line)
            
            # تحديث أو إنشاء دفتر الشريك
            ledger = PartnerLedger.query.filter_by(
                project_id=phase.project_id,
                partner_id=partner.id
            ).first()
            
            if ledger:
                ledger.balance = Decimal(str(partner_data['new_balance']))
            else:
                ledger = PartnerLedger(
                    id=generate_uid('PLEDG'),
                    project_id=phase.project_id,
                    partner_id=partner.id,
                    balance=Decimal(str(partner_data['new_balance']))
                )
                db.session.add(ledger)
        
        # تحديث حالة المرحلة
        phase.settled_at = datetime.now()
        
        # حفظ كل شيء
        db.session.commit()
        
        return {
            'success': True,
            'settlement': settlement,
            'message': f'تمت تسوية المرحلة "{phase.name}" بنجاح',
            'error': None
        }
        
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'settlement': None,
            'message': '',
            'error': f'خطأ في تنفيذ التسوية: {str(e)}'
        }


def get_project_ledger(project_id: str) -> List[Dict[str, Any]]:
    """
    جلب دفتر أرصدة جميع الشركاء في المشروع
    """
    ledgers = PartnerLedger.query.filter_by(project_id=project_id).all()
    
    result = []
    for ledger in ledgers:
        result.append({
            'partner': ledger.partner,
            'balance': float(ledger.balance),
            'status': 'دائن' if ledger.balance < 0 else ('مدين' if ledger.balance > 0 else 'متوازن'),
            'last_updated': ledger.last_updated
        })
    
    return sorted(result, key=lambda x: x['balance'], reverse=True)


def get_phase_expenses_details(phase_id: str) -> Dict[str, Any]:
    """
    جلب تفاصيل مصروفات المرحلة
    """
    phase = Phase.query.get(phase_id)
    if not phase:
        return None
    
    # المصروفات
    expenses = Expense.query.filter_by(phase_id=phase_id).order_by(Expense.expense_date.desc()).all()
    
    # المواد المصروفة
    material_issues = MaterialIssue.query.filter_by(phase_id=phase_id).order_by(MaterialIssue.issue_date.desc()).all()
    
    # تجميع حسب الشريك
    by_partner = {}
    
    for expense in expenses:
        partner_id = expense.paid_by_partner_id
        if partner_id not in by_partner:
            by_partner[partner_id] = {
                'partner': expense.paid_by,
                'expenses': 0,
                'materials': 0,
                'total': 0,
                'details': []
            }
        by_partner[partner_id]['expenses'] += float(expense.amount)
        by_partner[partner_id]['details'].append({
            'type': 'expense',
            'date': expense.expense_date,
            'amount': float(expense.amount),
            'description': expense.description,
            'category': expense.category
        })
    
    for issue in material_issues:
        if issue.issued_by_partner_id:
            partner_id = issue.issued_by_partner_id
            if partner_id not in by_partner:
                by_partner[partner_id] = {
                    'partner': issue.issued_by,
                    'expenses': 0,
                    'materials': 0,
                    'total': 0,
                    'details': []
                }
            cost = issue.total_cost
            by_partner[partner_id]['materials'] += cost
            by_partner[partner_id]['details'].append({
                'type': 'material',
                'date': issue.issue_date,
                'amount': cost,
                'description': f'{issue.quantity} {issue.material.unit} من {issue.material.name}',
                'category': 'مواد'
            })
    
    # حساب الإجمالي لكل شريك
    for partner_data in by_partner.values():
        partner_data['total'] = partner_data['expenses'] + partner_data['materials']
        # ترتيب التفاصيل حسب التاريخ
        partner_data['details'].sort(key=lambda x: x['date'], reverse=True)
    
    return {
        'phase': phase,
        'total_expenses': phase.total_expenses(),
        'total_materials': phase.total_materials(),
        'total_cost': phase.total_cost(),
        'expenses': expenses,
        'material_issues': material_issues,
        'by_partner': by_partner
    }