from app import app, db
from acc.models import Customer, Unit, Partner, Safe
from acc.services.utils import generate_uid

def seed_database():
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
        ]
        for p in partners:
            db.session.add(p)
        
        # Add some units
        units = [
            Unit(id=generate_uid('U'), code='A-1-101', name='101', floor='1', 
                building='A', area=120, unit_type='سكني', total_price=1500000, status='متاحة'),
            Unit(id=generate_uid('U'), code='A-2-201', name='201', floor='2', 
                building='A', area=150, unit_type='سكني', total_price=1800000, status='متاحة'),
            Unit(id=generate_uid('U'), code='B-1-101', name='101', floor='1', 
                building='B', area=100, unit_type='تجاري', total_price=2000000, status='متاحة'),
        ]
        for u in units:
            db.session.add(u)
        
        # Add default safe
        safe = Safe(id=generate_uid('S'), name='الخزنة الرئيسية', balance=0)
        db.session.add(safe)
        
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()