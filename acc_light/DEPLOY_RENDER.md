# دليل نشر التطبيق على Render

## الخطوات:

### 1. إنشاء حساب على Render
- اذهب إلى [render.com](https://render.com) وسجل حساب جديد
- يمكنك استخدام GitHub للتسجيل مباشرة

### 2. رفع الكود إلى GitHub
```bash
# في مجلد المشروع
git init
git add .
git commit -m "Initial commit"

# أنشئ مستودع جديد على GitHub
# ثم اربطه:
git remote add origin https://github.com/YOUR_USERNAME/acc-light.git
git branch -M main
git push -u origin main
```

### 3. النشر على Render - الطريقة الأولى (Render Dashboard)

#### أ. إنشاء قاعدة البيانات:
1. من Render Dashboard، اضغط على "New +"
2. اختر "PostgreSQL"
3. أدخل:
   - Name: `acc-light-db`
   - Database: `acc_light_db`
   - User: `acc_light_user`
   - Region: Oregon (US West)
4. اختر الخطة المجانية
5. اضغط "Create Database"

#### ب. نشر التطبيق:
1. اضغط "New +" مرة أخرى
2. اختر "Web Service"
3. اربط حساب GitHub إذا لم يكن مربوطاً
4. اختر مستودع `acc-light`
5. أدخل:
   - Name: `acc-light`
   - Region: Oregon (US West)
   - Branch: `main`
   - Runtime: Python
   - Build Command: `./build.sh`
   - Start Command: `gunicorn app:app`
6. اختر الخطة المجانية
7. أضف متغيرات البيئة:
   - اضغط "Advanced"
   - أضف "Add Environment Variable":
     - `DATABASE_URL`: (سيتم ملؤها تلقائياً من قاعدة البيانات)
     - `SECRET_KEY`: (اضغط "Generate" لإنشاء مفتاح عشوائي)
     - `FLASK_ENV`: `production`
8. اضغط "Create Web Service"

### 4. النشر على Render - الطريقة الثانية (render.yaml)

هذه طريقة أسهل لأننا أعددنا ملف `render.yaml`:

1. من Render Dashboard، اضغط "New +" → "Blueprint"
2. اربط مستودع GitHub
3. Render سيكتشف ملف `render.yaml` تلقائياً
4. راجع الإعدادات واضغط "Apply"
5. سيتم إنشاء قاعدة البيانات والتطبيق تلقائياً

### 5. بعد النشر

#### التحقق من عمل التطبيق:
- انتظر حتى يكتمل البناء (5-10 دقائق)
- ستحصل على رابط مثل: `https://acc-light.onrender.com`
- افتح الرابط للتأكد من عمل التطبيق

#### تشغيل الأوامر على الخادم:
من صفحة الخدمة في Render، اذهب إلى "Shell" وشغل:
```bash
# لإنشاء مستخدم إداري (إذا أضفت هذه الميزة)
flask create-admin

# لعرض السجلات
flask db current
```

### 6. نصائح مهمة:

1. **الخطة المجانية**:
   - التطبيق سيتوقف بعد 15 دقيقة من عدم النشاط
   - سيحتاج 30-60 ثانية للاستيقاظ عند الزيارة التالية
   - قاعدة البيانات محدودة بـ 1GB

2. **للإنتاج الحقيقي**:
   - قم بالترقية للخطة المدفوعة ($7/شهر)
   - أضف نطاق مخصص (Custom Domain)
   - فعّل النسخ الاحتياطي التلقائي

3. **المراقبة**:
   - تابع السجلات من "Logs" في لوحة التحكم
   - راقب استخدام الموارد من "Metrics"

### 7. تحديث التطبيق:
```bash
# عدّل الكود محلياً
git add .
git commit -m "Update feature X"
git push origin main

# Render سيكتشف التحديث وينشره تلقائياً
```

## متغيرات البيئة المطلوبة:
- `DATABASE_URL`: يتم توفيره تلقائياً من Render
- `SECRET_KEY`: مفتاح سري قوي
- `FLASK_ENV`: `production`

## استكشاف الأخطاء:

### إذا فشل البناء:
1. تحقق من سجلات البناء في Render
2. تأكد من أن `build.sh` قابل للتنفيذ
3. تحقق من إصدارات الحزم في `requirements.txt`

### إذا لم يعمل التطبيق:
1. تحقق من سجلات التطبيق
2. تأكد من أن `DATABASE_URL` محدد بشكل صحيح
3. جرب تشغيل `flask db upgrade` من Shell

### مشاكل قاعدة البيانات:
- Render يستخدم `postgres://` بينما SQLAlchemy يحتاج `postgresql://`
- هذا محلول في `config.py`