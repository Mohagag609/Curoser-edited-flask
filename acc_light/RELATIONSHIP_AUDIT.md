# SQLAlchemy Relationships Audit Report
## تقرير مراجعة علاقات SQLAlchemy

تاريخ: 2025-08-29

## المشاكل المكتشفة

### 1. تعارضات الأسماء (Name Conflicts)

#### 1.1 Unit Model (`unit.py`)
**المشكلة**: تعارض بين backref relationships و @property methods
- `Unit.contracts`: معرّف كـ backref في `Contract.unit` (السطر 34 في contract.py) وأيضاً كـ @property في Unit (السطر 46)
- `Unit.installments`: معرّف كـ backref في `Installment.unit` (السطر 13 في installment.py) وأيضاً كـ @property في Unit (السطر 51)

**السبب**: هذا يولّد SAWarning:
```
SAWarning: User-placed attribute Unit.contracts on Mapper[Unit(units)] is replacing an existing class-bound attribute
SAWarning: User-placed attribute Unit.installments on Mapper[Unit(units)] is replacing an existing class-bound attribute
```

**الحل المقترح**:
- إزالة @property methods من Unit model
- الاعتماد على backref relationships الموجودة

### 2. تكرار تعريف النماذج (Duplicate Model Definitions)

#### 2.1 Safe Model
**المشكلة**: تعريف مكرر في ملفين مختلفين
- `treasury.py`: يعرّف `Safe` و `SafeTransfer`
- `safe.py`: يعرّف `Safe` و `Transfer`

**الحل المقترح**:
- حذف `safe.py` بالكامل
- الاعتماد على `treasury.py` فقط
- التأكد من تحديث imports في باقي الملفات

### 3. أعمدة ForeignKey بدون suffix `_id`

معظم الأعمدة تتبع النمط الصحيح `name_id` لكن هناك استثناءات قليلة يجب مراجعتها للتأكد من عدم وجود تعارضات.

### 4. علاقات بدون back_populates أو backref متطابق

#### 4.1 Contract Model
- `commission_safe`: backref='contracts' قد يتعارض مع علاقات أخرى في Safe

#### 4.2 Inter-project transfers
- تحتاج مراجعة للتأكد من عدم تعارض backref names

### 5. علاقات Many-to-Many

لم أجد مشاكل واضحة في علاقات many-to-many الموجودة.

## الإصلاحات المطلوبة (بالترتيب)

### الأولوية 1: إصلاح تعارضات Unit (حرجة)

**الملف**: `acc/models/unit.py`

```python
# حذف هذه الأسطر (46-53):
@property 
def contracts(self):
    from acc.models import Contract
    return Contract.query.filter_by(unit_id=self.id).first()

@property
def installments(self):
    from acc.models import Installment
    return Installment.query.filter_by(unit_id=self.id).all()
```

**التعديل في calculate_remaining()**: 
- تغيير `self.contracts` إلى `self.contracts.first()` في السطر 57
- `self.installments` تبقى كما هي لأنها ستصبح relationship list

### الأولوية 2: حذف safe.py المكرر

**الإجراء**: حذف الملف `acc/models/safe.py` بالكامل

**تحديث imports**: البحث عن أي import من safe.py وتحويله إلى treasury.py

### الأولوية 3: مراجعة backref names للتأكد من عدم التعارض

**Contract.commission_safe**: 
- backref='contracts' قد يتعارض مع Safe.contracts من project relationship
- **الحل**: تغيير إلى backref='commission_contracts'

## اختبارات التحقق المقترحة

```python
# test_relationships.py
import pytest
from app import app, db
from acc.models import Unit, Contract, Installment, Customer

def test_unit_relationships():
    """Test Unit relationships work correctly"""
    with app.app_context():
        # Create test data
        unit = Unit(id='U1', code='U001', name='Test Unit', 
                   floor='1', building='A', total_price=100000)
        db.session.add(unit)
        
        customer = Customer(id='C1', name='Test Customer')
        db.session.add(customer)
        
        contract = Contract(id='CT1', code='CT001', unit_id='U1', 
                          customer_id='C1', total_price=100000,
                          start_date=datetime.now().date())
        db.session.add(contract)
        
        installment = Installment(id='I1', unit_id='U1', 
                                installment_number=1, amount=10000)
        db.session.add(installment)
        
        db.session.commit()
        
        # Test relationships
        assert unit.contracts.count() == 1
        assert unit.contracts.first().id == 'CT1'
        assert unit.installments.count() == 1
        assert unit.installments[0].id == 'I1'
        
        # Test reverse relationships
        assert contract.unit.id == 'U1'
        assert installment.unit.id == 'U1'
```

## ملفات النسخ الاحتياطي المطلوبة

قبل تطبيق أي تغييرات، يجب عمل نسخ احتياطية:
- `unit.py.bak.20250829`
- `safe.py.bak.20250829` (قبل الحذف)
- `contract.py.bak.20250829`

## Migration مطلوب

لا يوجد migration مطلوب لقاعدة البيانات لأن التغييرات في Python code فقط.

## التأثير المتوقع

بعد تطبيق هذه الإصلاحات:
1. ستختفي تحذيرات SAWarning
2. العلاقات ستعمل بشكل صحيح
3. لن يكون هناك تعارض في الأسماء
4. الكود سيكون أنظف وأكثر وضوحاً

## الخطوات التالية

1. موافقة على التغييرات المقترحة
2. عمل نسخ احتياطية
3. تطبيق التغييرات
4. تشغيل الاختبارات
5. التحقق من اختفاء التحذيرات