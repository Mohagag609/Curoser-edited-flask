from app import db
from app.models import Installment, Contract, Customer
from app.services.utils import get_current_date
from sqlalchemy import func, desc, asc
from datetime import date, timedelta


class InstallmentService:
    """خدمة إدارة الأقساط"""
    
    @staticmethod
    def create_installment(contract_id, installment_number, amount, due_date, notes=None):
        """إنشاء قسط جديد"""
        try:
            # التحقق من وجود العقد
            contract = Contract.get_by_id(contract_id)
            if not contract:
                raise ValueError("العقد غير موجود")
            
            installment = Installment(
                id=generate_code('INS', 6),
                contract_id=contract_id,
                installment_number=installment_number,
                amount=amount,
                due_date=due_date,
                status='معلق',
                notes=notes
            )
            
            installment.save()
            return installment
        except Exception as e:
            raise e
    
    @staticmethod
    def get_installment_by_id(installment_id):
        """الحصول على قسط بالمعرف"""
        return Installment.get_by_id(installment_id)
    
    @staticmethod
    def get_all_installments(status=None, contract_id=None):
        """الحصول على جميع الأقساط"""
        query = Installment.query
        if status:
            query = query.filter_by(status=status)
        if contract_id:
            query = query.filter_by(contract_id=contract_id)
        return query.order_by(Installment.due_date).all()
    
    @staticmethod
    def get_pending_installments(contract_id=None):
        """الحصول على الأقساط المعلقة"""
        query = Installment.query.filter_by(status='معلق')
        if contract_id:
            query = query.filter_by(contract_id=contract_id)
        return query.order_by(Installment.due_date).all()
    
    @staticmethod
    def get_paid_installments(contract_id=None):
        """الحصول على الأقساط المدفوعة"""
        query = Installment.query.filter_by(status='مدفوع')
        if contract_id:
            query = query.filter_by(contract_id=contract_id)
        return query.order_by(desc(Installment.payment_date)).all()
    
    @staticmethod
    def get_overdue_installments(contract_id=None):
        """الحصول على الأقساط المتأخرة"""
        query = Installment.query.filter(
            Installment.status == 'معلق',
            Installment.due_date < date.today()
        )
        if contract_id:
            query = query.filter_by(contract_id=contract_id)
        return query.order_by(Installment.due_date).all()
    
    @staticmethod
    def get_upcoming_installments(days_ahead=30, contract_id=None):
        """الحصول على الأقساط القادمة"""
        future_date = date.today() + timedelta(days=days_ahead)
        query = Installment.query.filter(
            Installment.status == 'معلق',
            Installment.due_date >= date.today(),
            Installment.due_date <= future_date
        )
        if contract_id:
            query = query.filter_by(contract_id=contract_id)
        return query.order_by(Installment.due_date).all()
    
    @staticmethod
    def pay_installment(installment_id, payment_date=None, payment_method=None, 
                       payment_reference=None, notes=None):
        """دفع قسط"""
        try:
            installment = Installment.get_by_id(installment_id)
            if not installment:
                raise ValueError("القسط غير موجود")
            
            if installment.status == 'مدفوع':
                raise ValueError("القسط مدفوع مسبقاً")
            
            # تسجيل الدفع
            installment.mark_as_paid(payment_date, payment_method, payment_reference)
            
            # تحديث ملاحظات القسط
            if notes:
                installment.notes = notes
                installment.save()
            
            return installment
        except Exception as e:
            raise e
    
    @staticmethod
    def cancel_payment(installment_id):
        """إلغاء دفع قسط"""
        try:
            installment = Installment.get_by_id(installment_id)
            if not installment:
                raise ValueError("القسط غير موجود")
            
            if installment.status != 'مدفوع':
                raise ValueError("القسط غير مدفوع")
            
            installment.mark_as_pending()
            return installment
        except Exception as e:
            raise e
    
    @staticmethod
    def update_installment(installment_id, **kwargs):
        """تحديث قسط"""
        try:
            installment = Installment.get_by_id(installment_id)
            if not installment:
                return None
            
            for key, value in kwargs.items():
                if hasattr(installment, key):
                    setattr(installment, key, value)
            
            installment.save()
            return installment
        except Exception as e:
            raise e
    
    @staticmethod
    def delete_installment(installment_id):
        """حذف قسط"""
        try:
            installment = Installment.get_by_id(installment_id)
            if not installment:
                return False
            
            if installment.status == 'مدفوع':
                raise ValueError("لا يمكن حذف قسط مدفوع")
            
            installment.delete()
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def get_installment_statistics(installment_id):
        """الحصول على إحصائيات القسط"""
        installment = Installment.get_by_id(installment_id)
        if not installment:
            return None
        
        stats = {
            'is_paid': installment.is_paid,
            'is_pending': installment.is_pending,
            'is_overdue': installment.is_overdue,
            'days_overdue': installment.days_overdue,
            'amount': float(installment.amount) if installment.amount else 0,
            'due_date': installment.due_date.isoformat() if installment.due_date else None,
            'payment_date': installment.payment_date.isoformat() if installment.payment_date else None
        }
        
        return stats
    
    @staticmethod
    def get_contract_installments_summary(contract_id):
        """الحصول على ملخص أقساط العقد"""
        contract = Contract.get_by_id(contract_id)
        if not contract:
            return None
        
        # إجمالي الأقساط
        total_installments = Installment.query.filter_by(contract_id=contract_id).count()
        
        # الأقساط المدفوعة
        paid_installments = Installment.query.filter_by(
            contract_id=contract_id, status='مدفوع'
        ).count()
        
        # الأقساط المعلقة
        pending_installments = Installment.query.filter_by(
            contract_id=contract_id, status='معلق'
        ).count()
        
        # الأقساط المتأخرة
        overdue_installments = Installment.query.filter(
            Installment.contract_id == contract_id,
            Installment.status == 'معلق',
            Installment.due_date < date.today()
        ).count()
        
        # إجمالي المبلغ المدفوع
        total_paid = db.session.query(func.sum(Installment.amount)).filter_by(
            contract_id=contract_id, status='مدفوع'
        ).scalar() or 0
        
        # إجمالي المبلغ المعلق
        total_pending = db.session.query(func.sum(Installment.amount)).filter_by(
            contract_id=contract_id, status='معلق'
        ).scalar() or 0
        
        # إجمالي المبلغ المتأخر
        total_overdue = db.session.query(func.sum(Installment.amount)).filter(
            Installment.contract_id == contract_id,
            Installment.status == 'معلق',
            Installment.due_date < date.today()
        ).scalar() or 0
        
        summary = {
            'total_installments': total_installments,
            'paid_installments': paid_installments,
            'pending_installments': pending_installments,
            'overdue_installments': overdue_installments,
            'total_paid': float(total_paid),
            'total_pending': float(total_pending),
            'total_overdue': float(total_overdue),
            'payment_percentage': round((paid_installments / total_installments * 100) if total_installments > 0 else 0, 2)
        }
        
        return summary
    
    @staticmethod
    def get_customer_installments_summary(customer_id):
        """الحصول على ملخص أقساط العميل"""
        customer = Customer.get_by_id(customer_id)
        if not customer:
            return None
        
        # إجمالي الأقساط
        total_installments = db.session.query(Installment).join(Contract).filter(
            Contract.customer_id == customer_id
        ).count()
        
        # الأقساط المدفوعة
        paid_installments = db.session.query(Installment).join(Contract).filter(
            Contract.customer_id == customer_id,
            Installment.status == 'مدفوع'
        ).count()
        
        # الأقساط المعلقة
        pending_installments = db.session.query(Installment).join(Contract).filter(
            Contract.customer_id == customer_id,
            Installment.status == 'معلق'
        ).count()
        
        # الأقساط المتأخرة
        overdue_installments = db.session.query(Installment).join(Contract).filter(
            Contract.customer_id == customer_id,
            Installment.status == 'معلق',
            Installment.due_date < date.today()
        ).count()
        
        # إجمالي المبلغ المدفوع
        total_paid = db.session.query(func.sum(Installment.amount)).join(Contract).filter(
            Contract.customer_id == customer_id,
            Installment.status == 'مدفوع'
        ).scalar() or 0
        
        # إجمالي المبلغ المعلق
        total_pending = db.session.query(func.sum(Installment.amount)).join(Contract).filter(
            Contract.customer_id == customer_id,
            Installment.status == 'معلق'
        ).scalar() or 0
        
        # إجمالي المبلغ المتأخر
        total_overdue = db.session.query(func.sum(Installment.amount)).join(Contract).filter(
            Contract.customer_id == customer_id,
            Installment.status == 'معلق',
            Installment.due_date < date.today()
        ).scalar() or 0
        
        summary = {
            'total_installments': total_installments,
            'paid_installments': paid_installments,
            'pending_installments': pending_installments,
            'overdue_installments': overdue_installments,
            'total_paid': float(total_paid),
            'total_pending': float(total_pending),
            'total_overdue': float(total_overdue),
            'payment_percentage': round((paid_installments / total_installments * 100) if total_installments > 0 else 0, 2)
        }
        
        return summary
    
    @staticmethod
    def get_installments_by_date_range(start_date, end_date, status=None):
        """الحصول على الأقساط في نطاق تاريخ معين"""
        query = Installment.query.filter(
            Installment.due_date >= start_date,
            Installment.due_date <= end_date
        )
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Installment.due_date).all()
    
    @staticmethod
    def get_installments_by_payment_date_range(start_date, end_date):
        """الحصول على الأقساط المدفوعة في نطاق تاريخ معين"""
        return Installment.query.filter(
            Installment.payment_date >= start_date,
            Installment.payment_date <= end_date,
            Installment.status == 'مدفوع'
        ).order_by(desc(Installment.payment_date)).all()
    
    @staticmethod
    def search_installments(search_term):
        """البحث في الأقساط"""
        query = Installment.query.join(Contract).join(Customer).filter(
            Installment.installment_number.contains(search_term) |
            Contract.code.contains(search_term) |
            Customer.name.contains(search_term)
        )
        return query.order_by(Installment.due_date).all()
    
    @staticmethod
    def get_installments_by_payment_method(payment_method):
        """الحصول على الأقساط حسب طريقة الدفع"""
        return Installment.query.filter_by(
            payment_method=payment_method, status='مدفوع'
        ).order_by(desc(Installment.payment_date)).all()
    
    @staticmethod
    def update_overdue_status():
        """تحديث حالة الأقساط المتأخرة"""
        try:
            overdue_installments = Installment.query.filter(
                Installment.status == 'معلق',
                Installment.due_date < date.today()
            ).all()
            
            for installment in overdue_installments:
                installment.status = 'متأخر'
                installment.save()
            
            return len(overdue_installments)
        except Exception as e:
            raise e