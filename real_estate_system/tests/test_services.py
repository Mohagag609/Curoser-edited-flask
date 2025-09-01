import unittest
from datetime import date
from app import create_app, db
from app.services.project_service import ProjectService
from app.services.customer_service import CustomerService
from app.services.unit_service import UnitService
from app.services.contract_service import ContractService


class TestServices(unittest.TestCase):
    """اختبار الخدمات"""
    
    def setUp(self):
        """إعداد الاختبار"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):
        """تنظيف بعد الاختبار"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_create_project(self):
        """اختبار إنشاء مشروع"""
        project = ProjectService.create_project(
            name='مشروع تجريبي',
            code='TEST001',
            project_type='عقاري',
            location='الرياض',
            status='نشط'
        )
        
        self.assertIsNotNone(project)
        self.assertEqual(project.name, 'مشروع تجريبي')
        self.assertEqual(project.code, 'TEST001')
        self.assertEqual(project.project_type, 'عقاري')
        self.assertEqual(project.location, 'الرياض')
        self.assertEqual(project.status, 'نشط')
    
    def test_create_customer(self):
        """اختبار إنشاء عميل"""
        customer = CustomerService.create_customer(
            name='عميل تجريبي',
            code='CUST001',
            phone='01234567890',
            national_id='12345678901234',
            status='نشط'
        )
        
        self.assertIsNotNone(customer)
        self.assertEqual(customer.name, 'عميل تجريبي')
        self.assertEqual(customer.code, 'CUST001')
        self.assertEqual(customer.phone, '01234567890')
        self.assertEqual(customer.national_id, '12345678901234')
        self.assertEqual(customer.status, 'نشط')
    
    def test_create_unit(self):
        """اختبار إنشاء وحدة"""
        # إنشاء مشروع أولاً
        project = ProjectService.create_project(
            name='مشروع تجريبي',
            code='TEST001',
            project_type='عقاري',
            status='نشط'
        )
        
        # إنشاء وحدة
        unit = UnitService.create_unit(
            project_id=project.id,
            name='وحدة تجريبية',
            code='UNIT001',
            unit_type='شقة',
            price=100000,
            status='متاح'
        )
        
        self.assertIsNotNone(unit)
        self.assertEqual(unit.name, 'وحدة تجريبية')
        self.assertEqual(unit.code, 'UNIT001')
        self.assertEqual(unit.unit_type, 'شقة')
        self.assertEqual(unit.price, 100000)
        self.assertEqual(unit.status, 'متاح')
        self.assertEqual(unit.project_id, project.id)
    
    def test_create_contract(self):
        """اختبار إنشاء عقد"""
        # إنشاء مشروع
        project = ProjectService.create_project(
            name='مشروع تجريبي',
            code='TEST001',
            project_type='عقاري',
            status='نشط'
        )
        
        # إنشاء عميل
        customer = CustomerService.create_customer(
            name='عميل تجريبي',
            code='CUST001',
            phone='01234567890',
            status='نشط'
        )
        
        # إنشاء وحدة
        unit = UnitService.create_unit(
            project_id=project.id,
            name='وحدة تجريبية',
            code='UNIT001',
            unit_type='شقة',
            price=100000,
            status='متاح'
        )
        
        # إنشاء عقد
        contract = ContractService.create_contract(
            unit_id=unit.id,
            customer_id=customer.id,
            total_price=100000,
            down_payment=10000,
            contract_date=date.today(),
            project_id=project.id
        )
        
        self.assertIsNotNone(contract)
        self.assertEqual(contract.total_price, 100000)
        self.assertEqual(contract.down_payment, 10000)
        self.assertEqual(contract.unit_id, unit.id)
        self.assertEqual(contract.customer_id, customer.id)
        self.assertEqual(contract.project_id, project.id)
        self.assertEqual(contract.status, 'نشط')
    
    def test_get_project_statistics(self):
        """اختبار إحصائيات المشروع"""
        # إنشاء مشروع
        project = ProjectService.create_project(
            name='مشروع تجريبي',
            code='TEST001',
            project_type='عقاري',
            status='نشط'
        )
        
        # إنشاء وحدة
        unit = UnitService.create_unit(
            project_id=project.id,
            name='وحدة تجريبية',
            code='UNIT001',
            unit_type='شقة',
            price=100000,
            status='متاح'
        )
        
        # الحصول على الإحصائيات
        stats = ProjectService.get_project_statistics(project.id)
        
        self.assertIsNotNone(stats)
        self.assertEqual(stats['total_units'], 1)
        self.assertEqual(stats['available_units'], 1)
        self.assertEqual(stats['sold_units'], 0)
        self.assertEqual(stats['completion_percentage'], 0)
    
    def test_get_customer_statistics(self):
        """اختبار إحصائيات العميل"""
        # إنشاء عميل
        customer = CustomerService.create_customer(
            name='عميل تجريبي',
            code='CUST001',
            phone='01234567890',
            status='نشط'
        )
        
        # الحصول على الإحصائيات
        stats = CustomerService.get_customer_statistics(customer.id)
        
        self.assertIsNotNone(stats)
        self.assertEqual(stats['total_contracts'], 0)
        self.assertEqual(stats['total_contracts_value'], 0)
        self.assertEqual(stats['total_paid_amount'], 0)
        self.assertEqual(stats['remaining_amount'], 0)


if __name__ == '__main__':
    unittest.main()