import os
from app import app, db
from acc.models import Customer, Unit, Partner, Safe, PartnerGroup, PartnerGroupMember, UnitPartner, Broker, Contract, Installment
from acc.services.utils import generate_uid
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def seed_database():
    # Skip seeding in production unless explicitly requested
    if os.environ.get('FLASK_ENV') == 'production' and not os.environ.get('FORCE_SEED'):
        print("Skipping seed in production. Set FORCE_SEED=1 to override.")
        return
        
    with app.app_context():
        # Check if data already exists
        if Customer.query.count() > 0:
            print("Database already has data. Skipping seed.")
            return
        
        print("Seeding database...")
        
        # Add some customers
        customers = [
            Customer(id=generate_uid('C'), name='أحمد محمد علي', phone='01012345678', 
                    national_id='29901011234567', address='القاهرة - مدينة نصر', status='نشط'),
            Customer(id=generate_uid('C'), name='محمد إبراهيم سالم', phone='01098765432', 
                    national_id='29801021234567', address='الجيزة - الهرم', status='نشط'),
            Customer(id=generate_uid('C'), name='فاطمة أحمد حسن', phone='01234567890', 
                    national_id='29701031234567', address='الإسكندرية', status='نشط'),
        ]
        for c in customers:
            db.session.add(c)
        
        # Add some partners
        partners = [
            Partner(id=generate_uid('PR'), name='مجموعة الأمل للاستثمار', phone='01111111111'),
            Partner(id=generate_uid('PR'), name='شركة النور العقارية', phone='01222222222'),
            Partner(id=generate_uid('PR'), name='أحمد السيد - مستثمر', phone='01333333333'),
            Partner(id=generate_uid('PR'), name='محمد إبراهيم - شريك', phone='01444444444'),
        ]
        db.session.add_all(partners)
        db.session.flush()  # To get IDs
        
        # Add partner groups
        group1 = PartnerGroup(id=generate_uid('PG'), name='مجموعة المستثمرين الرئيسيين')
        db.session.add(group1)
        db.session.flush()
        
        # Add members to group
        members = [
            PartnerGroupMember(group_id=group1.id, partner_id=partners[0].id, percentage=60),
            PartnerGroupMember(group_id=group1.id, partner_id=partners[1].id, percentage=40),
        ]
        db.session.add_all(members)
        
        # Add some units
        units = [
            Unit(id=generate_uid('U'), code='A-1-101', name='101', floor='1', 
                building='A', area=120, unit_type='سكني', total_price=1500000, status='متاحة'),
            Unit(id=generate_uid('U'), code='A-2-201', name='201', floor='2', 
                building='A', area=150, unit_type='سكني', total_price=1800000, status='متاحة'),
            Unit(id=generate_uid('U'), code='B-1-101', name='101', floor='1', 
                building='B', area=100, unit_type='تجاري', total_price=2000000, status='محجوزة'),
            Unit(id=generate_uid('U'), code='B-3-303', name='303', floor='3', 
                building='B', area=200, unit_type='سكني', total_price=2500000, status='متاحة'),
        ]
        db.session.add_all(units)
        db.session.flush()
        
        # Add partners to some units
        unit_partners = [
            UnitPartner(id=generate_uid('UP'), unit_id=units[0].id, partner_id=partners[0].id, percentage=60),
            UnitPartner(id=generate_uid('UP'), unit_id=units[0].id, partner_id=partners[1].id, percentage=40),
            UnitPartner(id=generate_uid('UP'), unit_id=units[2].id, partner_id=partners[2].id, percentage=100),
        ]
        db.session.add_all(unit_partners)
        
    # Add safes
    from acc.models import Safe
    safes = [
        Safe(id=generate_uid('SF'), name='الخزينة الرئيسية', type='cash', is_default=True),
        Safe(id=generate_uid('SF'), name='البنك الأهلي', type='bank', bank_name='البنك الأهلي المصري'),
    ]
    db.session.add_all(safes)
    db.session.flush()
    
    # Add brokers
    brokers = [
        Broker(id=generate_uid('BR'), name='أحمد الوسيط', phone='01555555555'),
        Broker(id=generate_uid('BR'), name='محمود السمسار', phone='01666666666'),
    ]
    db.session.add_all(brokers)
    db.session.flush()
        
    # Add contracts
    # Contract 1: Cash payment
    contract1 = Contract(
        id=generate_uid('CT'),
        code='2024-0001',
        customer_id=customers[0].id,
        unit_id=units[0].id,
        start_date=datetime.now().date() - timedelta(days=30),
        payment_type='cash',
        total_price=units[0].total_price,
        discount_amount=50000,
        down_payment=0,
        broker_name=brokers[0].name,
        broker_percent=2.5,
        broker_amount=units[0].total_price * 0.025,
        maintenance_deposit=10000,
        installment_count=0
    )
    db.session.add(contract1)
        
    # Contract 2: Installments
    contract2 = Contract(
        id=generate_uid('CT'),
        code='2024-0002',
        customer_id=customers[1].id,
        unit_id=units[2].id,
        start_date=datetime.now().date() - timedelta(days=15),
        payment_type='installment',
        total_price=units[2].total_price,
        discount_amount=0,
        down_payment=400000,
        broker_name=brokers[1].name,
        broker_percent=3.0,
        broker_amount=units[2].total_price * 0.03,
        maintenance_deposit=20000,
        installment_type='شهري',
        installment_count=24
    )
    db.session.add(contract2)
        
    # Update unit statuses
    units[0].status = 'مباعة'
    units[2].status = 'مباعة'
    
    db.session.flush()
    
    # Generate installments for contract2
    total_after_discount = contract2.total_price - contract2.discount_amount
    remaining_after_down = total_after_discount - contract2.down_payment
    installment_amount = remaining_after_down / contract2.installment_count
    start_date = contract2.start_date + timedelta(days=30)
    
    for i in range(contract2.installment_count):
        due_date = start_date + relativedelta(months=i)
        installment = Installment(
            id=generate_uid('INS'),
            unit_id=contract2.unit_id,
            installment_number=i + 1,
            type='شهري',
            original_amount=installment_amount,
            amount=installment_amount,
            due_date=due_date,
            status='غير مدفوع'
        )
        db.session.add(installment)
        
    db.session.commit()
    print("Database seeded successfully!")

if __name__ == '__main__':
    from app import app
    with app.app_context():
        seed_database()