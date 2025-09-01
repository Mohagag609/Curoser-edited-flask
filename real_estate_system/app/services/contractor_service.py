from app import db
from app.models import Contractor
from app.services.utils import generate_code


class ContractorService:
    """خدمة إدارة المقاولين"""
    
    @staticmethod
    def create_contractor(name, code=None, phone=None, national_id=None, 
                         address=None, email=None, notes=None, contact_person=None,
                         license_number=None, specialization=None):
        """إنشاء مقاول جديد"""
        try:
            # توليد كود إذا لم يتم توفيره
            if not code:
                code = generate_code('CON', 4)
            
            # التحقق من عدم تكرار الكود
            if Contractor.query.filter_by(code=code).first():
                code = generate_code('CON', 4)
            
            contractor = Contractor(
                id=generate_code('CON', 6),
                name=name,
                code=code,
                phone=phone,
                national_id=national_id,
                address=address,
                email=email,
                notes=notes,
                contact_person=contact_person,
                license_number=license_number,
                specialization=specialization,
                status='نشط'
            )
            
            contractor.save()
            return contractor
        except Exception as e:
            raise e
    
    @staticmethod
    def get_contractor_by_id(contractor_id):
        """الحصول على مقاول بالمعرف"""
        return Contractor.get_by_id(contractor_id)
    
    @staticmethod
    def get_all_contractors(status=None):
        """الحصول على جميع المقاولين"""
        query = Contractor.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Contractor.name).all()
    
    @staticmethod
    def get_active_contractors():
        """الحصول على المقاولين النشطين"""
        return Contractor.query.filter_by(status='نشط').order_by(Contractor.name).all()
    
    @staticmethod
    def update_contractor(contractor_id, **kwargs):
        """تحديث مقاول"""
        try:
            contractor = Contractor.get_by_id(contractor_id)
            if not contractor:
                return None
            
            for key, value in kwargs.items():
                if hasattr(contractor, key):
                    setattr(contractor, key, value)
            
            contractor.save()
            return contractor
        except Exception as e:
            raise e
    
    @staticmethod
    def delete_contractor(contractor_id):
        """حذف مقاول"""
        try:
            contractor = Contractor.get_by_id(contractor_id)
            if not contractor:
                return False
            
            # التحقق من وجود مشاريع
            if contractor.projects.count() > 0:
                raise ValueError("لا يمكن حذف المقاول لوجود مشاريع مرتبطة به")
            
            contractor.delete()
            return True
        except Exception as e:
            raise e