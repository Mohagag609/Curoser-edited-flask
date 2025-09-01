"""
إضافة حقول جديدة لجدول الأقساط (Installments) بطريقة متوافقة مع SQLite وPostgreSQL.

المنطق:
- نفحص الأعمدة الموجودة باستخدام SQLAlchemy Inspector.
- نضيف الأعمدة المفقودة (project_id, contract_id, customer_id) إن لم تكن موجودة.
- نعيد تسمية payment_date إلى paid_date إذا وُجدت الأولى ولم توجد الثانية.
"""

import os
import sys

# ضمان إمكانية استيراد حزمة المشروع عند التشغيل من مجلد "migrations"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from acc import create_app, db
from sqlalchemy import text, inspect


def _add_column(conn, dialect: str, table: str, column: str, sql_type: str):
    # SQLite و PostgreSQL كلاهما يدعمان ADD COLUMN الأساسي
    # نتجنب IF NOT EXISTS لأننا نتحقق برمجياً مسبقًا
    stmt = f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"
    conn.execute(text(stmt))


def _rename_column(conn, dialect: str, table: str, old: str, new: str):
    # كلاهما يدعم RENAME COLUMN في الإصدارات الحديثة
    stmt = f"ALTER TABLE {table} RENAME COLUMN {old} TO {new}"
    conn.execute(text(stmt))


def upgrade():
    app = create_app()

    with app.app_context():
        engine = db.engine
        dialect = engine.dialect.name  # 'sqlite' أو 'postgresql'

        with engine.begin() as conn:  # يضمن commit/rollback تلقائيًا
            inspector = inspect(conn)

            # تحقق من وجود الجدول أولًا
            tables = inspector.get_table_names()
            if 'installments' not in tables:
                print('⚠️ جدول installments غير موجود، لا توجد حاجة للترقية')
                return

            existing_columns = [c['name'] for c in inspector.get_columns('installments')]

            # الأعمدة المطلوب إضافتها
            to_add = []
            if 'project_id' not in existing_columns:
                to_add.append(('project_id', 'VARCHAR(20)'))
            if 'contract_id' not in existing_columns:
                to_add.append(('contract_id', 'VARCHAR(20)'))
            if 'customer_id' not in existing_columns:
                to_add.append(('customer_id', 'VARCHAR(20)'))

            for col_name, col_type in to_add:
                try:
                    _add_column(conn, dialect, 'installments', col_name, col_type)
                    print(f"✅ تمت إضافة العمود {col_name}")
                except Exception as e:
                    print(f"⚠️ تعذر إضافة العمود {col_name}: {e}")

            # إعادة تسمية payment_date إلى paid_date إذا لزم
            if 'payment_date' in existing_columns and 'paid_date' not in existing_columns:
                try:
                    _rename_column(conn, dialect, 'installments', 'payment_date', 'paid_date')
                    print("✅ تم تغيير اسم payment_date إلى paid_date")
                except Exception as e:
                    print(f"⚠️ تعذر تغيير اسم العمود: {e}")

        print("\n✅ تم تنفيذ ترقية جدول الأقساط بنجاح")


if __name__ == '__main__':
    upgrade()