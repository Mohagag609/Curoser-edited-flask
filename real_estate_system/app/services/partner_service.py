from app import db
from app.models import Partner
from app.services.utils import generate_code


class PartnerService:
    """خدمة إدارة الشركاء"""
    
    @staticmethod
    def create_partner(name, code=None, phone=None, national_id=None, 
                      address=None, email=None, notes=None, is_company=False,
                      company_registration=None, tax_number=None):
        """إنشاء شريك جديد"""
        try:
            # توليد كود إذا لم يتم توفيره
            if not code:
                code = generate_code('PAR', 4)
            
            # التحقق من عدم تكرار الكود
            if Partner.query.filter_by(code=code).first():
                code = generate_code('PAR', 4)
            
            partner = Partner(
                id=generate_code('PAR', 6),
                name=name,
                code=code,
                phone=phone,
                national_id=national_id,
                address=address,
                email=email,
                notes=notes,
                is_company=is_company,
                company_registration=company_registration,
                tax_number=tax_number,
                status='نشط'
            )
            
            partner.save()
            return partner
        except Exception as e:
            raise e
    
    @staticmethod
    def get_partner_by_id(partner_id):
        """الحصول على شريك بالمعرف"""
        return Partner.get_by_id(partner_id)
    
    @staticmethod
    def get_all_partners(status=None):
        """الحصول على جميع الشركاء"""
        query = Partner.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Partner.name).all()
    
    @staticmethod
    def get_active_partners():
        """الحصول على الشركاء النشطين"""
        return Partner.query.filter_by(status='نشط').order_by(Partner.name).all()
    
    @staticmethod
    def update_partner(partner_id, **kwargs):
        """تحديث شريك"""
        try:
            partner = Partner.get_by_id(partner_id)
            if not partner:
                return None
            
            for key, value in kwargs.items():
                if hasattr(partner, key):
                    setattr(partner, key, value)
            
            partner.save()
            return partner
        except Exception as e:
            raise e
    
    @staticmethod
    def delete_partner(partner_id):
        """حذف شريك"""
        try:
            partner = Partner.get_by_id(partner_id)
            if not partner:
                return False
            
            # التحقق من وجود وحدات أو ديون
            if partner.unit_partners.count() > 0 or partner.partner_debts.count() > 0:
                raise ValueError("لا يمكن حذف الشريك لوجود وحدات أو ديون مرتبطة به")
            
            partner.delete()
            return True
        except Exception as e:
            raise e