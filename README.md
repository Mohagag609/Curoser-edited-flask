# نظام إدارة المشاريع العقارية

نظام متكامل لإدارة المشاريع العقارية مبني بـ Flask + SQLAlchemy + HTMX + Tailwind CSS

## 🚀 المميزات

- إدارة متعددة المشاريع
- إدارة العملاء والعقود والوحدات
- نظام محاسبي متكامل
- تقارير شاملة
- نظام نسخ احتياطي تلقائي
- واجهة عربية حديثة

## 📋 المتطلبات

- Python 3.11+
- Node.js 18+
- SQLite3

## 🛠️ التثبيت

```bash
# Clone the repository
git clone [your-repo-url]
cd [project-folder]

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
npm install

# Build CSS
npm run build

# Create database tables
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Run database optimizations (optional but recommended)
python database_optimizations.py
```

## ▶️ التشغيل

### Development
```bash
python app.py
```

### Production (Gunicorn)
```bash
gunicorn app:app
```

## 💾 النسخ الاحتياطي

### إنشاء نسخة احتياطية
```bash
python backup_system.py create
```

### عرض النسخ الاحتياطية
```bash
python backup_system.py list
```

### استرجاع نسخة احتياطية
```bash
python backup_system.py restore backup_YYYYMMDD_HHMMSS.db.gz
```

## 📁 هيكل المشروع

```
.
├── app.py              # نقطة الدخول الرئيسية
├── config.py           # إعدادات التطبيق
├── requirements.txt    # Python dependencies
├── package.json        # Node dependencies
├── build.sh           # Render build script
├── acc/               # كود التطبيق الرئيسي
│   ├── models/        # نماذج قاعدة البيانات
│   ├── blueprints/    # Routes و Controllers
│   ├── services/      # Business logic
│   ├── static/        # CSS, JS, Images
│   └── templates/     # HTML templates
├── backups/           # مجلد النسخ الاحتياطية
└── database_optimizations.py  # تحسينات قاعدة البيانات
```

## 🔒 الأمان

- تأكد من تغيير `SECRET_KEY` في production
- استخدم HTTPS في production
- قم بعمل نسخ احتياطية دورية
- لا تشارك ملفات `.env` أو قاعدة البيانات

## 🤝 المساهمة

نرحب بالمساهمات! الرجاء فتح issue أو pull request.

## 📄 الترخيص

[Your License]