#!/usr/bin/env python3
"""تطبيق بسيط للاختبار بدون Flask"""

import json

# محاكاة رد بسيط
def simple_response():
    return {
        "status": "ok",
        "message": "التطبيق يعمل ولكن Flask غير مثبت",
        "solution": "يرجى تثبيت المتطلبات باستخدام: pip install -r requirements.txt"
    }

if __name__ == '__main__':
    print("🚀 التطبيق يعمل على http://localhost:5000")
    print("⚠️ هذا مجرد محاكاة - Flask غير مثبت")
    print(json.dumps(simple_response(), ensure_ascii=False, indent=2))
