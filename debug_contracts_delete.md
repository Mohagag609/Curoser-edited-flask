# دليل تشخيص مشكلة حذف العقود

## المشكلة
زر الحذف يعطي خطأ 404 أو 405

## خطوات التشخيص

### 1. افتح Console في المتصفح
- اضغط F12 أو كليك يمين > Inspect
- اذهب إلى تبويب Console
- جرب حذف عقد واحد

### 2. ما يجب البحث عنه في Console:
```
deleteContract called with: {contractId: "...", hasInstallments: ..., hasInstallmentsType: "..."}
Deleting contract: ... URL: /contracts/.../delete
Response status: ...
```

### 3. تحقق من Network Tab
- في Developer Tools، اذهب إلى Network
- جرب الحذف مرة أخرى
- ابحث عن طلب delete
- تحقق من:
  - Request URL
  - Request Method (يجب أن يكون POST)
  - Status Code (404 أو 405؟)
  - Response Headers

### 4. اختبار endpoint مباشرة
يمكنك اختبار endpoint في المتصفح مباشرة:
```
https://acc-light.onrender.com/contracts/[CONTRACT_ID]/delete_test
```
استبدل [CONTRACT_ID] برقم عقد حقيقي

### 5. المسارات المتاحة
- `/contracts/ID/delete` - مسار الحذف الرئيسي (POST)
- `/contracts/ID/delete_test` - مسار اختباري (GET/POST)
- `/contracts/ID/edit` - مسار التعديل
- `/contracts/ID` - مسار العرض

## الحلول المحتملة

### إذا كان الخطأ 404:
- تأكد من أن ID العقد صحيح
- تأكد من أن العقد موجود في المشروع الحالي

### إذا كان الخطأ 405:
- المشكلة في طريقة الطلب (Method)
- تأكد من أن الطلب POST وليس GET

## معلومات إضافية
- تم إضافة دعم لـ DELETE method بالإضافة إلى POST
- تم تحسين معالجة قيمة hasInstallments
- تم إضافة تسجيل أفضل في JavaScript و Python

## للمساعدة
شارك معي:
1. محتوى Console log
2. تفاصيل طلب Network
3. نتيجة اختبار delete_test endpoint