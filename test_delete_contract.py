#!/usr/bin/env python3
'''اختبار وظيفة حذف العقود'''

import requests
import json

# URL التطبيق
BASE_URL = 'http://localhost:5000'  # غيّر هذا حسب URL تطبيقك

def test_delete_contract(contract_id):
    '''اختبار حذف عقد'''
    print(f"🧪 اختبار حذف العقد: {contract_id}")
    
    # محاولة حذف العقد
    url = f"{BASE_URL}/contracts/{contract_id}/delete"
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, json={})
        print(f"📡 Status Code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ تم حذف العقد بنجاح!")
            else:
                print(f"❌ فشل الحذف: {data.get('message')}")
        else:
            print(f"❌ خطأ HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {str(e)}")

if __name__ == '__main__':
    # اختبار مع معرف عقد (غيّر هذا لمعرف عقد حقيقي)
    test_contract_id = 'CONTRACT-001'  # ضع معرف عقد حقيقي هنا
    test_delete_contract(test_contract_id)
