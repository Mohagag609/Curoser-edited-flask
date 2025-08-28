# نظام إدارة العقارات - ACC Light

نظام متقدم لإدارة العقارات مبني باستخدام Flask و HTMX و Tailwind CSS.

## المميزات

- إدارة شاملة للعملاء والوحدات والعقود
- نظام شركاء متقدم مع إدارة النسب والديون
- إدارة الأقساط والمدفوعات
- نظام خزينة متعدد مع السندات والتحويلات
- تقارير مالية وإدارية شاملة
- إدارة الموردين والمقاولين والمشاريع
- سجل شامل للتغييرات
- نظام نسخ احتياطي

## التثبيت

1. استنساخ المشروع:
```bash
git clone [repository-url]
cd acc_light
```

2. تثبيت الحزم المطلوبة:
```bash
pip install -r requirements.txt
npm install
```

3. إنشاء ملف البيئة:
```bash
cp .env.example .env
# قم بتحديث القيم في ملف .env
```

4. بناء ملفات CSS:
```bash
npm run build
```

5. إنشاء قاعدة البيانات:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## التشغيل

### بيئة التطوير:
```bash
# تشغيل خادم Flask
flask run

# في نافذة أخرى، تشغيل Tailwind في وضع المراقبة
npm run watch
```

### بيئة الإنتاج:
قم بتعيين متغيرات البيئة المناسبة وتشغيل التطبيق باستخدام خادم WSGI مثل Gunicorn.

## هيكل المشروع

```
acc_light/
├── acc/                    # حزمة التطبيق الرئيسية
│   ├── models/            # نماذج قاعدة البيانات
│   ├── blueprints/        # وحدات التطبيق
│   ├── services/          # منطق الأعمال
│   ├── templates/         # قوالب HTML
│   └── static/            # الملفات الثابتة
├── migrations/            # هجرات قاعدة البيانات
├── app.py                # نقطة دخول التطبيق
├── config.py             # إعدادات التطبيق
└── requirements.txt      # متطلبات Python
```

## التقنيات المستخدمة

- **Backend**: Flask, SQLAlchemy, Flask-Migrate
- **Frontend**: HTMX, Alpine.js, Tailwind CSS
- **Database**: SQLite (تطوير), PostgreSQL (إنتاج)

## المساهمة

نرحب بالمساهمات! يرجى قراءة دليل المساهمة قبل إرسال أي تغييرات.

## الترخيص

هذا المشروع مرخص تحت [رخصة MIT](LICENSE).