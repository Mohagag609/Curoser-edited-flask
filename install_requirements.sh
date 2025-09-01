#!/bin/bash
# سكريبت تثبيت متطلبات التطبيق

echo "🔧 تثبيت متطلبات التطبيق..."

# التحقق من وجود pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 غير مثبت. يرجى تثبيته أولاً."
    exit 1
fi

# محاولة تثبيت المتطلبات
echo "📦 تثبيت المتطلبات..."

# تثبيت Flask ومتطلباته
pip3 install --user Flask==3.0.0 || echo "⚠️ فشل تثبيت Flask"
pip3 install --user Flask-SQLAlchemy==3.1.1 || echo "⚠️ فشل تثبيت Flask-SQLAlchemy"
pip3 install --user python-dotenv==1.0.0 || echo "⚠️ فشل تثبيت python-dotenv"
pip3 install --user Jinja2==3.1.2 || echo "⚠️ فشل تثبيت Jinja2"
pip3 install --user gunicorn==21.2.0 || echo "⚠️ فشل تثبيت gunicorn"
pip3 install --user python-dateutil==2.8.2 || echo "⚠️ فشل تثبيت python-dateutil"

# محاولة تثبيت psycopg2-binary (قد يفشل بدون PostgreSQL)
echo "📦 محاولة تثبيت psycopg2-binary..."
pip3 install --user psycopg2-binary==2.9.9 2>/dev/null || {
    echo "⚠️ فشل تثبيت psycopg2-binary - سيتم استخدام SQLite"
}

echo "✅ انتهى تثبيت المتطلبات!"
echo ""
echo "📌 لتشغيل التطبيق:"
echo "   python3 app.py"
