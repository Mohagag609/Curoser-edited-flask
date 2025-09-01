from app import db
from app.models import Project, Unit, Contract, Customer
from app.services.utils import generate_code, get_current_date
from sqlalchemy import func, desc, asc


class ProjectService:
    """خدمة إدارة المشاريع"""
    
    @staticmethod
    def create_project(name, code=None, description=None, project_type='عقاري', 
                      location=None, area=None, contractor_id=None, 
                      start_date=None, expected_end_date=None, budget=None):
        """إنشاء مشروع جديد"""
        try:
            # توليد كود إذا لم يتم توفيره
            if not code:
                code = generate_code('PRJ', 4)
            
            # التحقق من عدم تكرار الكود
            if Project.query.filter_by(code=code).first():
                code = generate_code('PRJ', 4)
            
            project = Project(
                id=generate_code('PRJ', 6),
                name=name,
                code=code,
                description=description,
                project_type=project_type,
                location=location,
                area=area,
                contractor_id=contractor_id,
                start_date=start_date,
                expected_end_date=expected_end_date,
                budget=budget,
                status='نشط'
            )
            
            project.save()
            return project
        except Exception as e:
            raise e
    
    @staticmethod
    def get_project_by_id(project_id):
        """الحصول على مشروع بالمعرف"""
        return Project.get_by_id(project_id)
    
    @staticmethod
    def get_all_projects(status=None):
        """الحصول على جميع المشاريع"""
        query = Project.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Project.name).all()
    
    @staticmethod
    def get_active_projects():
        """الحصول على المشاريع النشطة"""
        return Project.query.filter_by(status='نشط').order_by(Project.name).all()
    
    @staticmethod
    def get_default_project():
        """الحصول على المشروع الافتراضي"""
        return Project.query.filter_by(is_default=True).first()
    
    @staticmethod
    def set_default_project(project_id):
        """تعيين مشروع كافتراضي"""
        try:
            # إلغاء الافتراضي من جميع المشاريع
            Project.query.update({'is_default': False})
            
            # تعيين المشروع الجديد كافتراضي
            project = Project.get_by_id(project_id)
            if project:
                project.is_default = True
                project.save()
                return True
            return False
        except Exception as e:
            raise e
    
    @staticmethod
    def update_project(project_id, **kwargs):
        """تحديث مشروع"""
        try:
            project = Project.get_by_id(project_id)
            if not project:
                return None
            
            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            
            project.save()
            return project
        except Exception as e:
            raise e
    
    @staticmethod
    def delete_project(project_id):
        """حذف مشروع"""
        try:
            project = Project.get_by_id(project_id)
            if not project:
                return False
            
            # التحقق من وجود وحدات أو عقود
            if project.units.count() > 0 or project.contracts.count() > 0:
                raise ValueError("لا يمكن حذف المشروع لوجود وحدات أو عقود مرتبطة به")
            
            project.delete()
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def get_project_statistics(project_id):
        """الحصول على إحصائيات المشروع"""
        project = Project.get_by_id(project_id)
        if not project:
            return None
        
        stats = {
            'total_units': project.total_units,
            'sold_units': project.sold_units,
            'available_units': project.available_units,
            'total_contracts_value': project.total_contracts_value,
            'completion_percentage': project.completion_percentage,
            'total_contracts': project.contracts.count(),
            'active_contracts': project.contracts.filter_by(status='نشط').count(),
            'cancelled_contracts': project.contracts.filter_by(status='ملغي').count()
        }
        
        return stats
    
    @staticmethod
    def get_project_units_by_status(project_id, status):
        """الحصول على وحدات المشروع حسب الحالة"""
        project = Project.get_by_id(project_id)
        if not project:
            return []
        
        return project.get_units_by_status(status)
    
    @staticmethod
    def get_project_contracts_by_status(project_id, status):
        """الحصول على عقود المشروع حسب الحالة"""
        project = Project.get_by_id(project_id)
        if not project:
            return []
        
        return project.get_contracts_by_status(status)
    
    @staticmethod
    def get_project_financial_summary(project_id):
        """الحصول على الملخص المالي للمشروع"""
        project = Project.get_by_id(project_id)
        if not project:
            return None
        
        # إجمالي قيمة الوحدات
        total_units_value = db.session.query(func.sum(Unit.price)).filter_by(
            project_id=project_id
        ).scalar() or 0
        
        # إجمالي قيمة العقود
        total_contracts_value = db.session.query(func.sum(Contract.total_price)).filter_by(
            project_id=project_id
        ).scalar() or 0
        
        # إجمالي المدفوع
        total_paid = db.session.query(func.sum(Contract.total_price)).join(
            Contract.installments
        ).filter(
            Contract.project_id == project_id,
            Contract.installments.any(status='مدفوع')
        ).scalar() or 0
        
        summary = {
            'total_units_value': float(total_units_value),
            'total_contracts_value': float(total_contracts_value),
            'total_paid': float(total_paid),
            'remaining_amount': float(total_contracts_value - total_paid),
            'sales_percentage': round((total_contracts_value / total_units_value * 100) if total_units_value > 0 else 0, 2)
        }
        
        return summary
    
    @staticmethod
    def search_projects(search_term):
        """البحث في المشاريع"""
        query = Project.query.filter(
            Project.name.contains(search_term) |
            Project.code.contains(search_term) |
            Project.location.contains(search_term)
        )
        return query.order_by(Project.name).all()
    
    @staticmethod
    def get_projects_by_contractor(contractor_id):
        """الحصول على مشاريع المقاول"""
        return Project.query.filter_by(contractor_id=contractor_id).order_by(Project.name).all()
    
    @staticmethod
    def get_projects_by_type(project_type):
        """الحصول على مشاريع حسب النوع"""
        return Project.query.filter_by(project_type=project_type).order_by(Project.name).all()


def get_current_project():
    """الحصول على المشروع الحالي"""
    return ProjectService.get_default_project()