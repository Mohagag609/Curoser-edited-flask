from app import db
from app.models import Customer, Contract, Installment
from app.services.utils import generate_code, validate_national_id, validate_phone, validate_email
from sqlalchemy import func, desc, asc


class CustomerService:
    """خدمة إدارة العملاء"""
    
    @staticmethod
    def create_customer(name, code=None, phone=None, national_id=None, 
                       address=None, notes=None):
        """إنشاء عميل جديد"""
        try:
            # التحقق من صحة البيانات
            if national_id and not validate_national_id(national_id):
                raise ValueError("الرقم القومي غير صحيح")
            
            if phone and not validate_phone(phone):
                raise ValueError("رقم الهاتف غير صحيح")
            
            # توليد كود إذا لم يتم توفيره
            if not code:
                code = generate_code('CUS', 4)
            
            # التحقق من عدم تكرار الكود
            if Customer.query.filter_by(code=code).first():
                code = generate_code('CUS', 4)
            
            # التحقق من عدم تكرار الرقم القومي
            if national_id and Customer.query.filter_by(national_id=national_id).first():
                raise ValueError("الرقم القومي مسجل مسبقاً")
            
            customer = Customer(
                id=generate_code('CUS', 6),
                name=name,
                code=code,
                phone=phone,
                national_id=national_id,
                address=address,
                notes=notes,
                status='نشط'
            )
            
            customer.save()
            return customer
        except Exception as e:
            raise e
    
    @staticmethod
    def get_customer_by_id(customer_id):
        """الحصول على عميل بالمعرف"""
        return Customer.get_by_id(customer_id)
    
    @staticmethod
    def get_customer_by_national_id(national_id):
        """الحصول على عميل بالرقم القومي"""
        return Customer.query.filter_by(national_id=national_id).first()
    
    @staticmethod
    def get_all_customers(status=None):
        """الحصول على جميع العملاء"""
        query = Customer.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Customer.name).all()
    
    @staticmethod
    def get_active_customers():
        """الحصول على العملاء النشطين"""
        return Customer.query.filter_by(status='نشط').order_by(Customer.name).all()
    
    @staticmethod
    def update_customer(customer_id, **kwargs):
        """تحديث عميل"""
        try:
            customer = Customer.get_by_id(customer_id)
            if not customer:
                return None
            
            # التحقق من صحة البيانات
            if 'national_id' in kwargs and kwargs['national_id']:
                if not validate_national_id(kwargs['national_id']):
                    raise ValueError("الرقم القومي غير صحيح")
                
                # التحقق من عدم تكرار الرقم القومي
                existing_customer = Customer.query.filter_by(national_id=kwargs['national_id']).first()
                if existing_customer and existing_customer.id != customer_id:
                    raise ValueError("الرقم القومي مسجل مسبقاً")
            
            if 'phone' in kwargs and kwargs['phone']:
                if not validate_phone(kwargs['phone']):
                    raise ValueError("رقم الهاتف غير صحيح")
            
            for key, value in kwargs.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
            
            customer.save()
            return customer
        except Exception as e:
            raise e
    
    @staticmethod
    def delete_customer(customer_id):
        """حذف عميل"""
        try:
            customer = Customer.get_by_id(customer_id)
            if not customer:
                return False
            
            # التحقق من وجود عقود
            if customer.contracts.count() > 0:
                raise ValueError("لا يمكن حذف العميل لوجود عقود مرتبطة به")
            
            customer.delete()
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def get_customer_statistics(customer_id):
        """الحصول على إحصائيات العميل"""
        customer = Customer.get_by_id(customer_id)
        if not customer:
            return None
        
        stats = {
            'total_contracts': customer.total_contracts,
            'total_contracts_value': customer.total_contracts_value,
            'total_paid_amount': customer.total_paid_amount,
            'remaining_amount': customer.remaining_amount,
            'active_contracts': customer.contracts.filter_by(status='نشط').count(),
            'cancelled_contracts': customer.contracts.filter_by(status='ملغي').count()
        }
        
        return stats
    
    @staticmethod
    def get_customer_contracts_by_status(customer_id, status):
        """الحصول على عقود العميل حسب الحالة"""
        customer = Customer.get_by_id(customer_id)
        if not customer:
            return []
        
        return customer.get_contracts_by_status(status)
    
    @staticmethod
    def get_customer_installments_by_status(customer_id, status):
        """الحصول على أقساط العميل حسب الحالة"""
        customer = Customer.get_by_id(customer_id)
        if not customer:
            return []
        
        return customer.get_installments_by_status(status)
    
    @staticmethod
    def get_customer_payment_history(customer_id):
        """الحصول على تاريخ مدفوعات العميل"""
        customer = Customer.get_by_id(customer_id)
        if not customer:
            return []
        
        # الحصول على جميع الأقساط المدفوعة
        paid_installments = db.session.query(Installment).join(Contract).filter(
            Contract.customer_id == customer_id,
            Installment.status == 'مدفوع'
        ).order_by(desc(Installment.payment_date)).all()
        
        return paid_installments
    
    @staticmethod
 def get_customer_overdue_installments(customer_id):
        """الحصول على الأقساط المتأخرة للعميل"""
        customer = Customer.get_by_id(customer_id)
        if not customer:
            return []
        
        from datetime import date
        overdue_installments = db.session.query(Installment).join(Contract).filter(
            Contract.customer_id == customer_id,
            Installment.status == 'معلق',
            Installment.due_date < date.today()
        ).order_by(Installment.due_date).all()
        
        return overdue_installments
    
    @staticmethod
    def get_customer_next_installments(customer_id, limit=5):
        """الحصول على الأقساط القادمة للعميل"""
        customer = Customer.get_by_id(customer_id)
        if not customer:
            return []
        
        from datetime import date
        next_installments = db.session.query(Installment).join(Contract).filter(
            Contract.customer_id == customer_id,
            Installment.status == 'معلق',
            Installment.due_date >= date.today()
        ).order_by(Installment.due_date).limit(limit).all()
        
        return next_installments
    
    @staticmethod
    def search_customers(search_term):
        """البحث في العملاء"""
        query = Customer.query.filter(
            Customer.name.contains(search_term) |
            Customer.code.contains(search_term) |
            Customer.phone.contains(search_term) |
            Customer.national_id.contains(search_term)
        )
        return query.order_by(Customer.name).all()
    
    @staticmethod
    def get_top_customers_by_value(limit=10):
        """الحصول على أفضل العملاء حسب القيمة"""
        customers = db.session.query(Customer).join(Contract).group_by(Customer.id).order_by(
            desc(func.sum(Contract.total_price))
        ).limit(limit).all()
        
        return customers
    
    @staticmethod
    def get_customers_with_overdue_payments():
        """الحصول على العملاء الذين لديهم أقساط متأخرة"""
        from datetime import date
        customers = db.session.query(Customer).join(Contract).join(Installment).filter(
            Installment.status == 'معلق',
            Installment.due_date < date.today()
        ).distinct().all()
        
        return customers
    
    @staticmethod
    def get_customer_financial_summary(customer_id):
        """الحصول على الملخص المالي للعميل"""
        customer = Customer.get_by_id(customer_id)
        if not customer:
            return None
        
        # إجمالي المدفوع
        total_paid = db.session.query(func.sum(Installment.amount)).join(Contract).filter(
            Contract.customer_id == customer_id,
            Installment.status == 'مدفوع'
        ).scalar() or 0
        
        # إجمالي المستحق
        total_due = db.session.query(func.sum(Installment.amount)).join(Contract).filter(
            Contract.customer_id == customer_id,
            Installment.status == 'معلق'
        ).scalar() or 0
        
        # إجمالي المتأخر
        from datetime import date
        total_overdue = db.session.query(func.sum(Installment.amount)).join(Contract).filter(
            Contract.customer_id == customer_id,
            Installment.status == 'معلق',
            Installment.due_date < date.today()
        ).scalar() or 0
        
        summary = {
            'total_contracts_value': customer.total_contracts_value,
            'total_paid': float(total_paid),
            'total_due': float(total_due),
            'total_overdue': float(total_overdue),
            'remaining_amount': customer.remaining_amount,
            'payment_percentage': round((total_paid / customer.total_contracts_value * 100) if customer.total_contracts_value > 0 else 0, 2)
        }
        
        return summary