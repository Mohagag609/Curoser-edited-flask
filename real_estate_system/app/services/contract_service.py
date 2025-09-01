from app import db
from app.models import Contract, Installment, Unit, Customer, Project
from app.services.utils import generate_code, calculate_installment_amount, get_current_date
from sqlalchemy import func, desc, asc
from datetime import date, timedelta


class ContractService:
    """خدمة إدارة العقود"""
    
    @staticmethod
    def create_contract(unit_id, customer_id, total_price, down_payment=0, 
                       discount_amount=0, maintenance_deposit=0, broker_name=None,
                       broker_percent=0, broker_amount=0, commission_safe_id=None,
                       contract_date=None, notes=None, project_id=None):
        """إنشاء عقد جديد"""
        try:
            # التحقق من وجود الوحدة والعميل
            unit = Unit.get_by_id(unit_id)
            customer = Customer.get_by_id(customer_id)
            
            if not unit:
                raise ValueError("الوحدة غير موجودة")
            
            if not customer:
                raise ValueError("العميل غير موجود")
            
            # التحقق من أن الوحدة متاحة
            if unit.status != 'متاح':
                raise ValueError("الوحدة غير متاحة للبيع")
            
            # توليد كود العقد
            contract_code = generate_code('CNT', 4)
            
            # التحقق من عدم تكرار الكود
            if Contract.query.filter_by(code=contract_code).first():
                contract_code = generate_code('CNT', 4)
            
            # إنشاء العقد
            contract = Contract(
                id=generate_code('CNT', 6),
                project_id=project_id or unit.project_id,
                code=contract_code,
                unit_id=unit_id,
                customer_id=customer_id,
                total_price=total_price,
                down_payment=down_payment,
                discount_amount=discount_amount,
                maintenance_deposit=maintenance_deposit,
                broker_name=broker_name,
                broker_percent=broker_percent,
                broker_amount=broker_amount,
                commission_safe_id=commission_safe_id,
                contract_date=contract_date or get_current_date(),
                notes=notes,
                status='نشط'
            )
            
            contract.save()
            
            # تحديث حالة الوحدة
            unit.status = 'مباع'
            unit.save()
            
            return contract
        except Exception as e:
            raise e
    
    @staticmethod
    def get_contract_by_id(contract_id):
        """الحصول على عقد بالمعرف"""
        return Contract.get_by_id(contract_id)
    
    @staticmethod
    def get_contract_by_code(contract_code):
        """الحصول على عقد بالكود"""
        return Contract.query.filter_by(code=contract_code).first()
    
    @staticmethod
    def get_all_contracts(status=None, project_id=None):
        """الحصول على جميع العقود"""
        query = Contract.query
        if status:
            query = query.filter_by(status=status)
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.order_by(desc(Contract.contract_date)).all()
    
    @staticmethod
    def get_active_contracts(project_id=None):
        """الحصول على العقود النشطة"""
        query = Contract.query.filter_by(status='نشط')
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.order_by(desc(Contract.contract_date)).all()
    
    @staticmethod
    def update_contract(contract_id, **kwargs):
        """تحديث عقد"""
        try:
            contract = Contract.get_by_id(contract_id)
            if not contract:
                return None
            
            for key, value in kwargs.items():
                if hasattr(contract, key):
                    setattr(contract, key, value)
            
            contract.save()
            return contract
        except Exception as e:
            raise e
    
    @staticmethod
    def cancel_contract(contract_id, reason=None):
        """إلغاء عقد"""
        try:
            contract = Contract.get_by_id(contract_id)
            if not contract:
                return False
            
            # إلغاء العقد
            contract.cancel_contract(reason)
            
            # تحديث حالة الوحدة
            unit = contract.unit
            unit.status = 'متاح'
            unit.save()
            
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def delete_contract(contract_id):
        """حذف عقد"""
        try:
            contract = Contract.get_by_id(contract_id)
            if not contract:
                return False
            
            # التحقق من وجود أقساط مدفوعة
            if contract.installments.filter_by(status='مدفوع').count() > 0:
                raise ValueError("لا يمكن حذف العقد لوجود أقساط مدفوعة")
            
            # تحديث حالة الوحدة
            unit = contract.unit
            unit.status = 'متاح'
            unit.save()
            
            contract.delete()
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def create_installments(contract_id, number_of_installments, start_date=None, 
                           installment_interval=30):
        """إنشاء أقساط للعقد"""
        try:
            contract = Contract.get_by_id(contract_id)
            if not contract:
                raise ValueError("العقد غير موجود")
            
            # حساب مبلغ القسط
            installment_amount = calculate_installment_amount(
                contract.total_price,
                contract.down_payment,
                number_of_installments
            )
            
            # تاريخ بداية الأقساط
            if not start_date:
                start_date = get_current_date() + timedelta(days=30)
            
            # إنشاء الأقساط
            installments = []
            for i in range(number_of_installments):
                installment_date = start_date + timedelta(days=i * installment_interval)
                
                installment = Installment(
                    id=generate_code('INS', 6),
                    contract_id=contract_id,
                    installment_number=f"{i+1}",
                    amount=installment_amount,
                    due_date=installment_date,
                    status='معلق'
                )
                
                installment.save()
                installments.append(installment)
            
            return installments
        except Exception as e:
            raise e
    
    @staticmethod
    def get_contract_statistics(contract_id):
        """الحصول على إحصائيات العقد"""
        contract = Contract.get_by_id(contract_id)
        if not contract:
            return None
        
        stats = {
            'total_installments': contract.total_installments,
            'paid_installments': contract.paid_installments,
            'pending_installments': contract.pending_installments,
            'paid_amount': contract.paid_amount,
            'remaining_amount': contract.remaining_amount,
            'payment_percentage': contract.payment_percentage,
            'is_fully_paid': contract.is_fully_paid
        }
        
        return stats
    
    @staticmethod
    def get_contract_installments_by_status(contract_id, status):
        """الحصول على أقساط العقد حسب الحالة"""
        contract = Contract.get_by_id(contract_id)
        if not contract:
            return []
        
        return contract.get_installments_by_status(status)
    
    @staticmethod
    def get_contract_next_installment(contract_id):
        """الحصول على القسط التالي للعقد"""
        contract = Contract.get_by_id(contract_id)
        if not contract:
            return None
        
        return contract.get_next_installment()
    
    @staticmethod
    def get_contract_overdue_installments(contract_id):
        """الحصول على الأقساط المتأخرة للعقد"""
        contract = Contract.get_by_id(contract_id)
        if not contract:
            return []
        
        return contract.get_overdue_installments()
    
    @staticmethod
    def search_contracts(search_term):
        """البحث في العقود"""
        query = Contract.query.join(Unit).join(Customer).filter(
            Contract.code.contains(search_term) |
            Unit.name.contains(search_term) |
            Customer.name.contains(search_term)
        )
        return query.order_by(desc(Contract.contract_date)).all()
    
    @staticmethod
    def get_contracts_by_customer(customer_id):
        """الحصول على عقود العميل"""
        return Contract.query.filter_by(customer_id=customer_id).order_by(desc(Contract.contract_date)).all()
    
    @staticmethod
    def get_contracts_by_unit(unit_id):
        """الحصول على عقود الوحدة"""
        return Contract.query.filter_by(unit_id=unit_id).order_by(desc(Contract.contract_date)).all()
    
    @staticmethod
    def get_contracts_by_project(project_id):
        """الحصول على عقود المشروع"""
        return Contract.query.filter_by(project_id=project_id).order_by(desc(Contract.contract_date)).all()
    
    @staticmethod
    def get_contracts_with_overdue_installments():
        """الحصول على العقود التي لديها أقساط متأخرة"""
        from datetime import date
        contracts = db.session.query(Contract).join(Installment).filter(
            Installment.status == 'معلق',
            Installment.due_date < date.today()
        ).distinct().all()
        
        return contracts
    
    @staticmethod
    def get_contracts_financial_summary(project_id=None):
        """الحصول على الملخص المالي للعقود"""
        query = Contract.query
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        # إجمالي قيمة العقود
        total_contracts_value = db.session.query(func.sum(Contract.total_price)).filter(
            query.whereclause
        ).scalar() or 0
        
        # إجمالي المدفوع
        total_paid = db.session.query(func.sum(Installment.amount)).join(Contract).filter(
            Installment.status == 'مدفوع',
            query.whereclause
        ).scalar() or 0
        
        # إجمالي المستحق
        total_due = db.session.query(func.sum(Installment.amount)).join(Contract).filter(
            Installment.status == 'معلق',
            query.whereclause
        ).scalar() or 0
        
        # إجمالي المتأخر
        from datetime import date
        total_overdue = db.session.query(func.sum(Installment.amount)).join(Contract).filter(
            Installment.status == 'معلق',
            Installment.due_date < date.today(),
            query.whereclause
        ).scalar() or 0
        
        summary = {
            'total_contracts': query.count(),
            'total_contracts_value': float(total_contracts_value),
            'total_paid': float(total_paid),
            'total_due': float(total_due),
            'total_overdue': float(total_overdue),
            'remaining_amount': float(total_contracts_value - total_paid),
            'payment_percentage': round((total_paid / total_contracts_value * 100) if total_contracts_value > 0 else 0, 2)
        }
        
        return summary