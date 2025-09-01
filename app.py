#!/usr/bin/env python3
"""
نقطة الدخول الرئيسية للتطبيق - متوافق مع Render
"""
import os
from acc import create_app

# إنشاء التطبيق
app = create_app()

if __name__ == '__main__':
    # تشغيل التطبيق
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )