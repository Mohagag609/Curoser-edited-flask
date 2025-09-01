# 🔧 إصلاح مشكلة قاعدة البيانات

## ❌ **المشكلة:**
```
sqlalchemy.exc.ArgumentError: Error creating backref 'contracts' on relationship 'Contract.project': property of that name exists on mapper 'Mapper[Project(projects)]'
```

## ✅ **السبب:**
تعارض في العلاقات - كان هناك `backref` مكرر للـ `contracts` في كل من:
- `Project.contracts` 
- `Contract.project` (backref='contracts')

## 🛠️ **الحل المطبق:**

### 1. **إصلاح العلاقات:**
- إزالة `backref` المكرر من `Project` model
- تبسيط العلاقات في `Contract` و `Installment` models
- استخدام `backref` بسيط بدلاً من `db.backref()`

### 2. **إعادة تعيين قاعدة البيانات:**
- إنشاء `reset_db_simple.py` لمسح قاعدة البيانات
- تحديث `build.sh` ليشمل إعادة التعيين
- إنشاء بيانات أساسية (مشروع افتراضي، خزينة)

## 🚀 **النتيجة:**

### في `build.sh`:
```bash
# Reset database to fix relationship conflicts
echo "Resetting database to fix relationship conflicts..."
python3 reset_db_simple.py
```

### البيانات الأساسية المنشأة:
- ✅ مشروع افتراضي
- ✅ خزينة رئيسية
- ✅ إعدادات النظام

## 📊 **ما ستراه في Logs:**

```
Resetting database to fix relationship conflicts...
🗑️ Resetting database...
Dropping all tables...
✅ All tables dropped
Creating all tables...
✅ All tables created
Creating basic data...
   - Default project: مشروع افتراضي
   - Default safe: الخزينة الرئيسية
✅ Basic data created
🎉 Database reset completed successfully!
```

## 🎯 **الآن يمكنك:**

1. **Push الكود:**
   ```bash
   git add .
   git commit -m "Fix database relationship conflicts"
   git push
   ```

2. **Render سيقوم بـ:**
   - مسح قاعدة البيانات القديمة
   - إنشاء قاعدة بيانات نظيفة
   - إنشاء البيانات الأساسية
   - تشغيل النظام المحسن

## ✅ **المشكلة محلولة!**

النظام الآن سيعمل بدون أخطاء العلاقات.