import unittest
from app import create_app, db
from app.models import Project, Customer, Unit, Contract, Installment


class TestModels(unittest.TestCase):
    """اختبار النماذج"""
    
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
        project = Project(
            id='PRJ001',
            name='مشروع تجريبي',
            code='TEST001',
            project_type='عقاري',
            status='نشط'
        )
        db.session.add(project)
        db.session.commit()
        
        self.assertEqual(project.name, 'مشروع تجريبي')
        self.assertEqual(project.code, 'TEST001')
        self.assertEqual(project.status, 'نشط')
    
    def test_create_customer(self):
        """اختبار إنشاء عميل"""
        customer = Customer(
            id='CUS001',
            name='عميل تجريبي',
            code='CUST001',
            phone='01234567890',
            status='نشط'
        )
        db.session.add(customer)
        db.session.commit()
        
        self.assertEqual(customer.name, 'عميل تجريبي')
        self.assertEqual(customer.phone, '01234567890')
        self.assertEqual(customer.status, 'نشط')
    
    def test_create_unit(self):
        """اختبار إنشاء وحدة"""
        # إنشاء مشروع أولاً
        project = Project(
            id='PRJ001',
            name='مشروع تجريبي',
            code='TEST001',
            project_type='عقاري',
            status='نشط'
        )
        db.session.add(project)
        db.session.commit()
        
        # إنشاء وحدة
        unit = Unit(
            id='UNT001',
            project_id='PRJ001',
            name='وحدة تجريبية',
            code='UNIT001',
            price=100000,
            status='متاح'
        )
        db.session.add(unit)
        db.session.commit()
        
        self.assertEqual(unit.name, 'وحدة تجريبية')
        self.assertEqual(unit.price, 100000)
        self.assertEqual(unit.status, 'متاح')
        self.assertEqual(unit.project_id, 'PRJ001')
    
    def test_create_contract(self):
        """اختبار إنشاء عقد"""
        # إنشاء مشروع
        project = Project(
            id='PRJ001',
            name='مشروع تجريبي',
            code='TEST001',
            project_type='عقاري',
            status='نشط'
        )
        db.session.add(project)
        
        # إنشاء عميل
        customer = Customer(
            id='CUS001',
            name='عميل تجريبي',
            code='CUST001',
            phone='01234567890',
            status='نشط'
        )
        db.session.add(customer)
        
        # إنشاء وحدة
        unit = Unit(
            id='UNT001',
            project_id='PRJ001',
            name='وحدة تجريبية',
            code='UNIT001',
            price=100000,
            status='متاح'
        )
        db.session.add(unit)
        db.session.commit()
        
        # إنشاء عقد
        contract = Contract(
            id='CNT001',
            project_id='PRJ001',
            code='CONTRACT001',
            unit_id='UNT001',
            customer_id='CUS001',
            total_price=100000,
            status='نشط'
        )
        db.session.add(contract)
        db.session.commit()
        
        self.assertEqual(contract.code, 'CONTRACT001')
        self.assertEqual(contract.total_price, 100000)
        self.assertEqual(contract.status, 'نشط')
        self.assertEqual(contract.unit_id, 'UNT001')
        self.assertEqual(contract.customer_id, 'CUS001')
    
    def test_create_installment(self):
        """اختبار إنشاء قسط"""
        # إنشاء عقد أولاً
        project = Project(
            id='PRJ001',
            name='مشروع تجريبي',
            code='TEST001',
            project_type='عقاري',
            status='نشط'
        )
        db.session.add(project)
        
        customer = Customer(
            id='CUS001',
            name='عميل تجريبي',
            code='CUST001',
            phone='01234567890',
            status='نشط'
        )
        db.session.add(customer)
        
        unit = Unit(
            id='UNT001',
            project_id='PRJ001',
            name='وحدة تجريبية',
            code='UNIT001',
            price=100000,
            status='متاح'
        )
        db.session.add(unit)
        
        contract = Contract(
            id='CNT001',
            project_id='PRJ001',
            code='CONTRACT001',
            unit_id='UNT001',
            customer_id='CUS001',
            total_price=100000,
            status='نشط'
        )
        db.session.add(contract)
        db.session.commit()
        
        # إنشاء قسط
        installment = Installment(
            id='INS001',
            contract_id='CNT001',
            installment_number='1',
            amount=10000,
            status='معلق'
        )
        db.session.add(installment)
        db.session.commit()
        
        self.assertEqual(installment.installment_number, '1')
        self.assertEqual(installment.amount, 10000)
        self.assertEqual(installment.status, 'معلق')
        self.assertEqual(installment.contract_id, 'CNT001')


if __name__ == '__main__':
    unittest.main()