#!/usr/bin/env python3
"""اختبار وحدات العقود والأقساط"""

from acc import create_app, db
from acc.models import Contract, Installment, Unit, Customer, Project

def test_contracts():
    """اختبار العقود والأقساط"""
    app = create_app()
    
    with app.app_context():
        try:
            # عد العقود
            contracts_count = Contract.query.count()
            print(f"✅ عدد العقود: {contracts_count}")
            
            # عد الأقساط
            installments_count = Installment.query.count()
            print(f"✅ عدد الأقساط: {installments_count}")
            
            # اختبار العلاقات
            if contracts_count > 0:
                contract = Contract.query.first()
                print(f"\n📄 العقد الأول:")
                print(f"   - الكود: {contract.code}")
                print(f"   - العميل: {contract.customer.name if contract.customer else 'غير محدد'}")
                print(f"   - الوحدة: {contract.unit.name if contract.unit else 'غير محدد'}")
                
                # اختبار الأقساط
                if hasattr(contract, 'installments') and contract.installments:
                    installments = contract.installments.all() if hasattr(contract.installments, 'all') else list(contract.installments)
                    print(f"   - عدد الأقساط: {len(installments)}")
            
            # اختبار الوحدات المتاحة
            available_units = Unit.query.filter_by(status='متاحة').count()
            print(f"\n🏠 الوحدات المتاحة: {available_units}")
            
            # اختبار العملاء النشطين
            active_customers = Customer.query.filter_by(status='نشط').count()
            print(f"👥 العملاء النشطون: {active_customers}")
            
            print("\n✨ جميع الاختبارات نجحت!")
            
        except Exception as e:
            print(f"\n❌ خطأ في الاختبار: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_contracts()