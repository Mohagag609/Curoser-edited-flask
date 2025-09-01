from app import db
from app.models import Unit, Project, Contract, Partner, UnitPartner
from app.services.utils import generate_code
from sqlalchemy import func, desc, asc


class UnitService:
    """خدمة إدارة الوحدات"""
    
    @staticmethod
    def create_unit(project_id, name, code=None, unit_type=None, floor=None, 
                   area=None, price=None, description=None, features=None,
                   is_penthouse=False, is_ground_floor=False, has_balcony=False,
                   has_garden=False, has_parking=False, has_elevator=False):
        """إنشاء وحدة جديدة"""
        try:
            # التحقق من وجود المشروع
            project = Project.get_by_id(project_id)
            if not project:
                raise ValueError("المشروع غير موجود")
            
            # توليد كود إذا لم يتم توفيره
            if not code:
                code = generate_code('UNT', 4)
            
            # التحقق من عدم تكرار الكود في نفس المشروع
            if Unit.query.filter_by(project_id=project_id, code=code).first():
                code = generate_code('UNT', 4)
            
            unit = Unit(
                id=generate_code('UNT', 6),
                project_id=project_id,
                code=code,
                name=name,
                unit_type=unit_type,
                floor=floor,
                area=area,
                price=price,
                description=description,
                features=features,
                is_penthouse=is_penthouse,
                is_ground_floor=is_ground_floor,
                has_balcony=has_balcony,
                has_garden=has_garden,
                has_parking=has_parking,
                has_elevator=has_elevator,
                status='متاح'
            )
            
            unit.save()
            return unit
        except Exception as e:
            raise e
    
    @staticmethod
    def get_unit_by_id(unit_id):
        """الحصول على وحدة بالمعرف"""
        return Unit.get_by_id(unit_id)
    
    @staticmethod
    def get_unit_by_code(project_id, code):
        """الحصول على وحدة بالكود في مشروع معين"""
        return Unit.query.filter_by(project_id=project_id, code=code).first()
    
    @staticmethod
    def get_all_units(project_id=None, status=None):
        """الحصول على جميع الوحدات"""
        query = Unit.query
        if project_id:
            query = query.filter_by(project_id=project_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Unit.name).all()
    
    @staticmethod
    def get_available_units(project_id=None):
        """الحصول على الوحدات المتاحة"""
        query = Unit.query.filter_by(status='متاح')
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.order_by(Unit.name).all()
    
    @staticmethod
    def get_sold_units(project_id=None):
        """الحصول على الوحدات المباعة"""
        query = Unit.query.filter_by(status='مباع')
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.order_by(Unit.name).all()
    
    @staticmethod
    def get_reserved_units(project_id=None):
        """الحصول على الوحدات المحجوزة"""
        query = Unit.query.filter_by(status='محجوز')
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.order_by(Unit.name).all()
    
    @staticmethod
    def update_unit(unit_id, **kwargs):
        """تحديث وحدة"""
        try:
            unit = Unit.get_by_id(unit_id)
            if not unit:
                return None
            
            for key, value in kwargs.items():
                if hasattr(unit, key):
                    setattr(unit, key, value)
            
            unit.save()
            return unit
        except Exception as e:
            raise e
    
    @staticmethod
    def delete_unit(unit_id):
        """حذف وحدة"""
        try:
            unit = Unit.get_by_id(unit_id)
            if not unit:
                return False
            
            # التحقق من وجود عقود
            if unit.contracts.count() > 0:
                raise ValueError("لا يمكن حذف الوحدة لوجود عقود مرتبطة بها")
            
            unit.delete()
            return True
        except Exception as e:
            raise e
    
    @staticmethod
    def reserve_unit(unit_id, customer_id=None, notes=None):
        """حجز وحدة"""
        try:
            unit = Unit.get_by_id(unit_id)
            if not unit:
                raise ValueError("الوحدة غير موجودة")
            
            if unit.status != 'متاح':
                raise ValueError("الوحدة غير متاحة للحجز")
            
            unit.status = 'محجوز'
            unit.save()
            
            return unit
        except Exception as e:
            raise e
    
    @staticmethod
    def release_unit(unit_id):
        """إلغاء حجز وحدة"""
        try:
            unit = Unit.get_by_id(unit_id)
            if not unit:
                raise ValueError("الوحدة غير موجودة")
            
            if unit.status == 'محجوز':
                unit.status = 'متاح'
                unit.save()
            
            return unit
        except Exception as e:
            raise e
    
    @staticmethod
    def sell_unit(unit_id):
        """بيع وحدة"""
        try:
            unit = Unit.get_by_id(unit_id)
            if not unit:
                raise ValueError("الوحدة غير موجودة")
            
            if unit.status not in ['متاح', 'محجوز']:
                raise ValueError("الوحدة غير متاحة للبيع")
            
            unit.status = 'مباع'
            unit.save()
            
            return unit
        except Exception as e:
            raise e
    
    @staticmethod
    def get_unit_statistics(unit_id):
        """الحصول على إحصائيات الوحدة"""
        unit = Unit.get_by_id(unit_id)
        if not unit:
            return None
        
        stats = {
            'total_contracts': unit.total_contracts,
            'active_contract': unit.active_contract,
            'price_per_sqm': unit.price_per_sqm,
            'status': unit.status,
            'is_available': unit.is_available,
            'is_sold': unit.is_sold,
            'is_reserved': unit.is_reserved
        }
        
        return stats
    
    @staticmethod
    def get_unit_contracts_by_status(unit_id, status):
        """الحصول على عقود الوحدة حسب الحالة"""
        unit = Unit.get_by_id(unit_id)
        if not unit:
            return []
        
        return unit.get_contracts_by_status(status)
    
    @staticmethod
    def get_unit_partners(unit_id):
        """الحصول على شركاء الوحدة"""
        unit = Unit.get_by_id(unit_id)
        if not unit:
            return []
        
        return unit.get_partners()
    
    @staticmethod
    def add_partner_to_unit(unit_id, partner_id, percentage):
        """إضافة شريك للوحدة"""
        try:
            unit = Unit.get_by_id(unit_id)
            partner = Partner.get_by_id(partner_id)
            
            if not unit:
                raise ValueError("الوحدة غير موجودة")
            
            if not partner:
                raise ValueError("الشريك غير موجود")
            
            # التحقق من أن مجموع النسب لا يتجاوز 100%
            total_percentage = db.session.query(func.sum(UnitPartner.percentage)).filter_by(
                unit_id=unit_id
            ).scalar() or 0
            
            if total_percentage + percentage > 100:
                raise ValueError("مجموع نسب الشركاء لا يمكن أن يتجاوز 100%")
            
            return unit.add_partner(partner, percentage)
        except Exception as e:
            raise e
    
    @staticmethod
    def remove_partner_from_unit(unit_id, partner_id):
        """إزالة شريك من الوحدة"""
        try:
            unit = Unit.get_by_id(unit_id)
            partner = Partner.get_by_id(partner_id)
            
            if not unit:
                raise ValueError("الوحدة غير موجودة")
            
            if not partner:
                raise ValueError("الشريك غير موجود")
            
            return unit.remove_partner(partner)
        except Exception as e:
            raise e
    
    @staticmethod
    def search_units(search_term, project_id=None):
        """البحث في الوحدات"""
        query = Unit.query
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        query = query.filter(
            Unit.name.contains(search_term) |
            Unit.code.contains(search_term) |
            Unit.unit_type.contains(search_term)
        )
        
        return query.order_by(Unit.name).all()
    
    @staticmethod
    def get_units_by_type(unit_type, project_id=None):
        """الحصول على الوحدات حسب النوع"""
        query = Unit.query.filter_by(unit_type=unit_type)
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.order_by(Unit.name).all()
    
    @staticmethod
    def get_units_by_floor(floor, project_id=None):
        """الحصول على الوحدات حسب الطابق"""
        query = Unit.query.filter_by(floor=floor)
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.order_by(Unit.name).all()
    
    @staticmethod
    def get_units_by_price_range(min_price, max_price, project_id=None):
        """الحصول على الوحدات حسب نطاق السعر"""
        query = Unit.query.filter(Unit.price >= min_price, Unit.price <= max_price)
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.order_by(Unit.price).all()
    
    @staticmethod
    def get_units_by_area_range(min_area, max_area, project_id=None):
        """الحصول على الوحدات حسب نطاق المساحة"""
        query = Unit.query.filter(Unit.area >= min_area, Unit.area <= max_area)
        if project_id:
            query = query.filter_by(project_id=project_id)
        return query.order_by(Unit.area).all()
    
    @staticmethod
    def get_units_with_features(features, project_id=None):
        """الحصول على الوحدات التي تحتوي على مميزات معينة"""
        query = Unit.query
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        for feature in features:
            if hasattr(Unit, feature):
                query = query.filter(getattr(Unit, feature) == True)
        
        return query.order_by(Unit.name).all()
    
    @staticmethod
    def get_project_units_summary(project_id):
        """الحصول على ملخص وحدات المشروع"""
        project = Project.get_by_id(project_id)
        if not project:
            return None
        
        # إجمالي الوحدات
        total_units = Unit.query.filter_by(project_id=project_id).count()
        
        # الوحدات المتاحة
        available_units = Unit.query.filter_by(project_id=project_id, status='متاح').count()
        
        # الوحدات المباعة
        sold_units = Unit.query.filter_by(project_id=project_id, status='مباع').count()
        
        # الوحدات المحجوزة
        reserved_units = Unit.query.filter_by(project_id=project_id, status='محجوز').count()
        
        # إجمالي قيمة الوحدات
        total_value = db.session.query(func.sum(Unit.price)).filter_by(project_id=project_id).scalar() or 0
        
        # إجمالي قيمة الوحدات المباعة
        sold_value = db.session.query(func.sum(Unit.price)).filter_by(
            project_id=project_id, status='مباع'
        ).scalar() or 0
        
        summary = {
            'total_units': total_units,
            'available_units': available_units,
            'sold_units': sold_units,
            'reserved_units': reserved_units,
            'total_value': float(total_value),
            'sold_value': float(sold_value),
            'available_value': float(total_value - sold_value),
            'sales_percentage': round((sold_units / total_units * 100) if total_units > 0 else 0, 2)
        }
        
        return summary