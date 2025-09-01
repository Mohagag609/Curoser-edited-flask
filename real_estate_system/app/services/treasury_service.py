from app import db
from app.models import Safe, SafeTransfer, Voucher, Project
from app.services.utils import generate_code, get_current_date
from sqlalchemy import func, desc, asc


class TreasuryService:
    """خدمة إدارة الخزائن"""
    
    @staticmethod
    def create_safe(name, code=None, description=None, initial_balance=0, 
                   project_id=None, is_main=False):
        """إنشاء خزينة جديدة"""
        try:
            # توليد كود إذا لم يتم توفيره
            if not code:
                code = generate_code('SAF', 4)
            
            # التحقق من عدم تكرار الكود
            if Safe.query.filter_by(code=code).first():
                code = generate_code('SAF', 4)
            
            # إذا كانت الخزينة الرئيسية، إلغاء الرئيسية من جميع الخزائن
            if is_main:
                Safe.query.update({'is_main': False})
            
            safe = Safe(
                id=generate_code('SAF', 6),
                project_id=project_id,
                name=name,
                code=code,
                description=description,
                initial_balance=initial_balance,
                current_balance=initial_balance,
                is_main=is_main,
                status='نشط'
            )
            
            safe.save()
            return safe
        except Exception as e:
            raise e
    
    @staticmethod
    def get_safe_by_id(safe_id):
        """الحصول على خزينة بالمعرف"""
        return Safe.get_by_id(safe_id)
    
    @staticmethod
    def get_safe_by_code(code):
        """الحصول على خزينة بالكود"""
        return Safe.query.filter_by(code=code).first()
    
    @staticmethod
    def get_all_safes(project_id=None, status=None):
        """الحصول على جميع الخزائن"""
        query = Safe.query
        if project_id:
            query = query.filter_by(project_id=project_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Safe.name).all()
    
    @staticmethod
    def get_active_safes(project_id=None):
        """الحصول على الخزائن النشطة"""
        query = Safe.query.filter_by(status='نشط')
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.order_by(Safe.name).all()
    
    @staticmethod
    def get_main_safe():
        """الحصول على الخزينة الرئيسية"""
        return Safe.query.filter_by(is_main=True).first()
    
    @staticmethod
    def update_safe(safe_id, **kwargs):
        """تحديث خزينة"""
        try:
            safe = Safe.get_by_id(safe_id)
            if not safe:
                return None
            
            # إذا كانت الخزينة ستكون رئيسية، إلغاء الرئيسية من جميع الخزائن
            if kwargs.get('is_main', False):
                Safe.query.update({'is_main': False})
            
            for key, value in kwargs.items():
                if hasattr(safe, key):
                    setattr(safe, key, value)
            
            safe.save()
            return safe
        except Exception as e:
            raise e
    
    @staticmethod
    def delete_safe(safe_id):
        """حذف خزينة"""
        try:
            safe = Safe.get_by_id(safe_id)
            if not safe:
                return False
            
            # التحقق من وجود سندات
            if safe.vouchers.count() > 0:
                raise ValueError("لا يمكن حذف الخزينة لوجود سندات مرتبطة بها")
            
            safe.delete()
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def add_income(safe_id, amount, description=None, reference=None, voucher_date=None):
        """إضافة إيراد للخزينة"""
        try:
            safe = Safe.get_by_id(safe_id)
            if not safe:
                raise ValueError("الخزينة غير موجودة")
            
            voucher = safe.add_income(amount, description, reference)
            if voucher_date:
                voucher.voucher_date = voucher_date
                voucher.save()
            
            return voucher
        except Exception as e:
            raise e
    
    @staticmethod
    def add_expense(safe_id, amount, description=None, reference=None, voucher_date=None):
        """إضافة مصروف للخزينة"""
        try:
            safe = Safe.get_by_id(safe_id)
            if not safe:
                raise ValueError("الخزينة غير موجودة")
            
            voucher = safe.add_expense(amount, description, reference)
            if voucher_date:
                voucher.voucher_date = voucher_date
                voucher.save()
            
            return voucher
        except Exception as e:
            raise e
    
    @staticmethod
    def transfer_between_safes(from_safe_id, to_safe_id, amount, description=None):
        """تحويل بين الخزائن"""
        try:
            from_safe = Safe.get_by_id(from_safe_id)
            to_safe = Safe.get_by_id(to_safe_id)
            
            if not from_safe:
                raise ValueError("الخزينة المصدر غير موجودة")
            
            if not to_safe:
                raise ValueError("الخزينة الهدف غير موجودة")
            
            if from_safe_id == to_safe_id:
                raise ValueError("لا يمكن التحويل لنفس الخزينة")
            
            return from_safe.transfer_to(to_safe, amount, description)
        except Exception as e:
            raise e
    
    @staticmethod
    def get_safe_statistics(safe_id):
        """الحصول على إحصائيات الخزينة"""
        safe = Safe.get_by_id(safe_id)
        if not safe:
            return None
        
        stats = {
            'initial_balance': float(safe.initial_balance) if safe.initial_balance else 0,
            'current_balance': float(safe.current_balance) if safe.current_balance else 0,
            'total_income': safe.total_income,
            'total_expenses': safe.total_expenses,
            'net_balance': safe.net_balance,
            'total_vouchers': safe.vouchers.count(),
            'income_vouchers': safe.vouchers.filter_by(voucher_type='إيراد').count(),
            'expense_vouchers': safe.vouchers.filter_by(voucher_type='مصروف').count()
        }
        
        return stats
    
    @staticmethod
    def get_safe_vouchers_by_type(safe_id, voucher_type):
        """الحصول على سندات الخزينة حسب النوع"""
        safe = Safe.get_by_id(safe_id)
        if not safe:
            return []
        
        return safe.vouchers.filter_by(voucher_type=voucher_type).order_by(desc(Voucher.voucher_date)).all()
    
    @staticmethod
    def get_safe_transfers(safe_id):
        """الحصول على تحويلات الخزينة"""
        safe = Safe.get_by_id(safe_id)
        if not safe:
            return []
        
        # التحويلات الصادرة
        outgoing_transfers = safe.transfers_from.order_by(desc(SafeTransfer.created_at)).all()
        
        # التحويلات الواردة
        incoming_transfers = safe.transfers_to.order_by(desc(SafeTransfer.created_at)).all()
        
        return {
            'outgoing': outgoing_transfers,
            'incoming': incoming_transfers
        }
    
    @staticmethod
    def search_safes(search_term):
        """البحث في الخزائن"""
        query = Safe.query.filter(
            Safe.name.contains(search_term) |
            Safe.code.contains(search_term) |
            Safe.description.contains(search_term)
        )
        return query.order_by(Safe.name).all()
    
    @staticmethod
    def get_safes_by_project(project_id):
        """الحصول على خزائن المشروع"""
        return Safe.query.filter_by(project_id=project_id).order_by(Safe.name).all()
    
    @staticmethod
    def get_project_financial_summary(project_id):
        """الحصول على الملخص المالي للمشروع"""
        project = Project.get_by_id(project_id)
        if not project:
            return None
        
        # إجمالي الإيرادات
        total_income = db.session.query(func.sum(Voucher.amount)).join(Safe).filter(
            Safe.project_id == project_id,
            Voucher.voucher_type == 'إيراد'
        ).scalar() or 0
        
        # إجمالي المصروفات
        total_expenses = db.session.query(func.sum(Voucher.amount)).join(Safe).filter(
            Safe.project_id == project_id,
            Voucher.voucher_type == 'مصروف'
        ).scalar() or 0
        
        # إجمالي الأرصدة
        total_balances = db.session.query(func.sum(Safe.current_balance)).filter_by(
            project_id=project_id
        ).scalar() or 0
        
        summary = {
            'total_income': float(total_income),
            'total_expenses': float(total_expenses),
            'net_profit': float(total_income - total_expenses),
            'total_balances': float(total_balances),
            'total_safes': Safe.query.filter_by(project_id=project_id).count()
        }
        
        return summary
    
    @staticmethod
    def get_vouchers_by_date_range(start_date, end_date, safe_id=None, voucher_type=None):
        """الحصول على السندات في نطاق تاريخ معين"""
        query = Voucher.query.filter(
            Voucher.voucher_date >= start_date,
            Voucher.voucher_date <= end_date
        )
        
        if safe_id:
            query = query.filter_by(safe_id=safe_id)
        
        if voucher_type:
            query = query.filter_by(voucher_type=voucher_type)
        
        return query.order_by(desc(Voucher.voucher_date)).all()
    
    @staticmethod
    def get_vouchers_by_amount_range(min_amount, max_amount, safe_id=None, voucher_type=None):
        """الحصول على السندات في نطاق مبلغ معين"""
        query = Voucher.query.filter(
            Voucher.amount >= min_amount,
            Voucher.amount <= max_amount
        )
        
        if safe_id:
            query = query.filter_by(safe_id=safe_id)
        
        if voucher_type:
            query = query.filter_by(voucher_type=voucher_type)
        
        return query.order_by(desc(Voucher.amount)).all()
    
    @staticmethod
    def search_vouchers(search_term):
        """البحث في السندات"""
        query = Voucher.query.filter(
            Voucher.voucher_number.contains(search_term) |
            Voucher.description.contains(search_term) |
            Voucher.reference.contains(search_term)
        )
        return query.order_by(desc(Voucher.voucher_date)).all()
    
    @staticmethod
    def get_voucher_statistics(voucher_id):
        """الحصول على إحصائيات السند"""
        voucher = Voucher.get_by_id(voucher_id)
        if not voucher:
            return None
        
        stats = {
            'is_income': voucher.is_income,
            'is_expense': voucher.is_expense,
            'is_completed': voucher.is_completed,
            'amount': float(voucher.amount) if voucher.amount else 0,
            'voucher_date': voucher.voucher_date.isoformat() if voucher.voucher_date else None
        }
        
        return stats
    
    @staticmethod
    def update_safe_balances():
        """تحديث أرصدة جميع الخزائن"""
        try:
            safes = Safe.query.all()
            for safe in safes:
                safe.update_balance()
            
            return len(safes)
        except Exception as e:
            raise e