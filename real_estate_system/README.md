# نظام إدارة العقارات

نظام متكامل لإدارة المشاريع العقارية مبني بـ Flask + SQLAlchemy + Bootstrap 5

## 🚀 المميزات

- **إدارة متعددة المشاريع**: إدارة عدة مشاريع عقارية في نفس الوقت
- **إدارة العملاء**: قاعدة بيانات شاملة للعملاء مع معلومات الاتصال
- **إدارة الوحدات**: تتبع الوحدات المتاحة والمباعة والمحجوزة
- **إدارة العقود**: نظام عقود متكامل مع تفاصيل الدفع
- **إدارة الأقساط**: تتبع الأقساط المدفوعة والمعلقة والمتأخرة
- **إدارة الخزائن**: نظام خزائن متعدد مع تتبع الإيرادات والمصروفات
- **التقارير**: تقارير شاملة عن المبيعات والأداء المالي
- **واجهة عربية**: واجهة مستخدم باللغة العربية مع دعم RTL
- **تصميم متجاوب**: يعمل على جميع الأجهزة (كمبيوتر، تابلت، موبايل)

## 📋 المتطلبات

- Python 3.8+
- SQLite3 (أو PostgreSQL للإنتاج)
- متصفح ويب حديث

## 🛠️ التثبيت

### 1. استنساخ المشروع
```bash
git clone <repository-url>
cd real_estate_system
```

### 2. إنشاء بيئة افتراضية
```bash
python -m venv venv
source venv/bin/activate  # على Linux/Mac
# أو
venv\Scripts\activate  # على Windows
```

### 3. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 4. تشغيل التطبيق
```bash
python run.py
```

### 5. الوصول للتطبيق
افتح المتصفح وانتقل إلى: `http://localhost:5000`

## 📁 هيكل المشروع

```
real_estate_system/
├── app/                    # كود التطبيق الرئيسي
│   ├── models/            # نماذج قاعدة البيانات
│   ├── views/             # Controllers (Blueprints)
│   ├── services/          # Business Logic
│   ├── utils/             # Utilities و Helper Functions
│   ├── forms/             # WTForms
│   └── decorators/        # Custom Decorators
├── templates/             # HTML Templates
├── static/                # CSS, JS, Images
│   ├── css/
│   ├── js/
│   └── images/
├── config/                # إعدادات التطبيق
├── migrations/            # Database Migrations
├── tests/                 # Unit Tests
├── requirements.txt       # Python Dependencies
├── run.py                # نقطة الدخول الرئيسية
└── README.md             # هذا الملف
```

## 🗄️ قاعدة البيانات

النظام يستخدم SQLAlchemy ORM مع دعم لـ:
- SQLite (للتطوير)
- PostgreSQL (للإنتاج)
- MySQL (اختياري)

### النماذج الرئيسية:
- **Project**: المشاريع العقارية
- **Customer**: العملاء
- **Unit**: الوحدات العقارية
- **Contract**: العقود
- **Installment**: الأقساط
- **Safe**: الخزائن
- **Voucher**: السندات المالية

## 🔧 الإعدادات

### متغيرات البيئة
```bash
# إعدادات التطبيق
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# قاعدة البيانات
DATABASE_URL=sqlite:///real_estate.db

# إعدادات أخرى
ITEMS_PER_PAGE=20
SESSION_COOKIE_SECURE=False
```

### إعدادات الإنتاج
```bash
# قاعدة البيانات
DATABASE_URL=postgresql://user:password@localhost/real_estate

# الأمان
SECRET_KEY=your-production-secret-key
SESSION_COOKIE_SECURE=True
FLASK_DEBUG=False
```

## 📊 الاستخدام

### 1. إدارة المشاريع
- إنشاء مشاريع جديدة
- إضافة تفاصيل المشروع (الموقع، المساحة، المقاول)
- تعيين مشروع افتراضي

### 2. إدارة العملاء
- إضافة عملاء جدد
- تتبع معلومات الاتصال
- عرض تاريخ المعاملات

### 3. إدارة الوحدات
- إضافة وحدات للمشروع
- تتبع حالة الوحدة (متاح، محجوز، مباع)
- إضافة مميزات الوحدة

### 4. إدارة العقود
- إنشاء عقود جديدة
- ربط العميل بالوحدة
- تحديد شروط الدفع

### 5. إدارة الأقساط
- إنشاء جدول أقساط
- تتبع المدفوعات
- إشعارات الأقساط المتأخرة

### 6. إدارة الخزائن
- إنشاء خزائن متعددة
- تتبع الإيرادات والمصروفات
- تحويلات بين الخزائن

## 🔒 الأمان

- حماية CSRF
- تشفير كلمات المرور
- جلسات آمنة
- التحقق من صحة البيانات

## 🚀 النشر

### استخدام Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### استخدام Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

## 🧪 الاختبار

```bash
# تشغيل الاختبارات
python -m pytest tests/

# مع التغطية
python -m pytest --cov=app tests/
```

## 📈 الأداء

- فهرسة قاعدة البيانات
- تخزين مؤقت للاستعلامات
- تحسين الاستعلامات
- ضغط الملفات الثابتة

## 🤝 المساهمة

1. Fork المشروع
2. إنشاء فرع للميزة الجديدة
3. Commit التغييرات
4. Push للفرع
5. إنشاء Pull Request

## 📄 الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

## 📞 الدعم

للحصول على الدعم أو الإبلاغ عن مشاكل:
- إنشاء Issue في GitHub
- التواصل عبر البريد الإلكتروني

## 🔄 التحديثات

### الإصدار 1.0.0
- إطلاق النسخة الأولى
- جميع الميزات الأساسية
- واجهة عربية كاملة

---

**تم تطوير هذا النظام بعناية ليكون أداة شاملة لإدارة المشاريع العقارية. نتمنى أن يكون مفيداً لكم!**