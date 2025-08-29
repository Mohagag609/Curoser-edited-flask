from acc.extensions import db
from acc.models import InterProjectTransfer, Safe, Voucher, Project
from acc.services.utils import generate_uid, log_action
from datetime import datetime
from sqlalchemy import func


def create_inter_project_transfer(from_project_id, from_safe_id, to_project_id, to_safe_id, amount, notes=None):
    """
    إنشاء تحويل بين مشروعين
    
    Args:
        from_project_id: معرف المشروع المُرسل
        from_safe_id: معرف الخزينة المُرسلة
        to_project_id: معرف المشروع المُستقبل
        to_safe_id: معرف الخزينة المُستقبلة
        amount: المبلغ المحول
        notes: ملاحظات اختيارية
        
    Returns:
        tuple: (success, message, transfer)
    """
    try:
        # التحقق من المشاريع
        from_project = Project.query.get(from_project_id)
        to_project = Project.query.get(to_project_id)
        
        if not from_project or not to_project:
            return False, "المشروع غير موجود", None
            
        if from_project_id == to_project_id:
            return False, "لا يمكن التحويل لنفس المشروع", None
        
        # التحقق من الخزن
        from_safe = Safe.query.get(from_safe_id)
        to_safe = Safe.query.get(to_safe_id)
        
        if not from_safe or not to_safe:
            return False, "الخزينة غير موجودة", None
        
        # التحقق من الرصيد
        if from_safe.balance < amount:
            return False, f"الرصيد غير كافي. الرصيد المتاح: {from_safe.balance}", None
        
        # بدء المعاملة
        db.session.begin_nested()
        
        try:
            # 1. إنشاء سند صرف في المشروع المُرسل
            from_voucher = Voucher(
                id=generate_uid('V'),
                project_id=from_project_id,
                voucher_type='صرف',
                voucher_number=generate_voucher_number(from_project_id, 'صرف'),
                date=datetime.now(),
                safe_id=from_safe_id,
                amount=amount,
                description=f"تحويل إلى مشروع: {to_project.name}",
                recipient_name=f"مشروع {to_project.name}",
                payment_method='تحويل',
                reference_type='inter_project_transfer'
            )
            db.session.add(from_voucher)
            
            # 2. تحديث رصيد الخزينة المُرسلة
            from_safe.balance -= amount
            
            # 3. إنشاء سند قبض في المشروع المُستقبل
            to_voucher = Voucher(
                id=generate_uid('V'),
                project_id=to_project_id,
                voucher_type='قبض',
                voucher_number=generate_voucher_number(to_project_id, 'قبض'),
                date=datetime.now(),
                safe_id=to_safe_id,
                amount=amount,
                description=f"تحويل من مشروع: {from_project.name}",
                recipient_name=f"مشروع {from_project.name}",
                payment_method='تحويل',
                reference_type='inter_project_transfer'
            )
            db.session.add(to_voucher)
            
            # 4. تحديث رصيد الخزينة المُستقبلة
            to_safe.balance += amount
            
            # 5. إنشاء سجل التحويل
            transfer = InterProjectTransfer(
                from_project_id=from_project_id,
                from_safe_id=from_safe_id,
                to_project_id=to_project_id,
                to_safe_id=to_safe_id,
                amount=amount,
                notes=notes,
                from_voucher_id=from_voucher.id,
                to_voucher_id=to_voucher.id
            )
            db.session.add(transfer)
            
            # 6. تسجيل الحدث
            log_action('تحويل بين المشاريع', {
                'from_project': from_project.name,
                'to_project': to_project.name,
                'amount': amount,
                'transfer_id': transfer.id
            })
            
            db.session.commit()
            
            return True, "تم التحويل بنجاح", transfer
            
        except Exception as e:
            db.session.rollback()
            return False, f"خطأ في إنشاء التحويل: {str(e)}", None
            
    except Exception as e:
        return False, f"خطأ: {str(e)}", None


def generate_voucher_number(project_id, voucher_type):
    """توليد رقم سند فريد للمشروع"""
    prefix = 'R' if voucher_type == 'قبض' else 'P'
    
    # الحصول على آخر رقم سند في المشروع
    last_voucher = Voucher.query.filter_by(
        project_id=project_id,
        voucher_type=voucher_type
    ).order_by(Voucher.voucher_number.desc()).first()
    
    if last_voucher and last_voucher.voucher_number:
        try:
            last_number = int(last_voucher.voucher_number.split('-')[-1])
            new_number = last_number + 1
        except:
            new_number = 1
    else:
        new_number = 1
    
    return f"{prefix}-{new_number:06d}"


def get_project_transfers(project_id, transfer_type='all'):
    """
    الحصول على التحويلات الخاصة بمشروع
    
    Args:
        project_id: معرف المشروع
        transfer_type: 'in' للواردة، 'out' للصادرة، 'all' للكل
    """
    query = InterProjectTransfer.query
    
    if transfer_type == 'in':
        query = query.filter_by(to_project_id=project_id)
    elif transfer_type == 'out':
        query = query.filter_by(from_project_id=project_id)
    else:
        query = query.filter(
            db.or_(
                InterProjectTransfer.from_project_id == project_id,
                InterProjectTransfer.to_project_id == project_id
            )
        )
    
    return query.order_by(InterProjectTransfer.transfer_date.desc()).all()


def get_transfer_summary(project_id):
    """الحصول على ملخص التحويلات للمشروع"""
    # التحويلات الصادرة
    out_total = db.session.query(func.sum(InterProjectTransfer.amount)).filter_by(
        from_project_id=project_id
    ).scalar() or 0
    
    # التحويلات الواردة
    in_total = db.session.query(func.sum(InterProjectTransfer.amount)).filter_by(
        to_project_id=project_id
    ).scalar() or 0
    
    return {
        'total_in': in_total,
        'total_out': out_total,
        'net': in_total - out_total
    }