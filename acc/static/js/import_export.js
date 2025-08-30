// نظام الاستيراد والتصدير المتقدم
let selectedFile = null;
let previewData = null;
let currentEntity = 'customers'; // الكيان الحالي

// فتح نافذة الاستيراد/التصدير
function openImportExportModal(entity = 'customers') {
    currentEntity = entity;
    document.getElementById('importExportModal').classList.remove('hidden');
    resetModal();
}

// إغلاق النافذة
function closeImportExportModal() {
    document.getElementById('importExportModal').classList.add('hidden');
    resetModal();
}

// إعادة تعيين النافذة
function resetModal() {
    switchTab('import');
    showStep('upload');
    clearFile();
    document.getElementById('importResults').innerHTML = '';
    document.getElementById('previewTable').innerHTML = '';
}

// تبديل التبويبات
function switchTab(tab) {
    // إخفاء جميع المحتويات
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    
    // إزالة التفعيل من جميع التبويبات
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('border-b-2', 'border-blue-500', 'text-blue-600');
        btn.classList.add('text-gray-500');
    });
    
    // إظهار المحتوى المحدد
    document.getElementById(tab + 'Content').classList.remove('hidden');
    
    // تفعيل التبويب المحدد
    const activeTab = document.getElementById(tab + 'Tab');
    activeTab.classList.remove('text-gray-500');
    activeTab.classList.add('border-b-2', 'border-blue-500', 'text-blue-600');
}

// عرض خطوة معينة
function showStep(step) {
    document.querySelectorAll('.step-content').forEach(content => {
        content.classList.add('hidden');
    });
    document.getElementById(step + 'Step').classList.remove('hidden');
}

// معالجة السحب والإفلات
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

// منع السلوك الافتراضي للسحب والإفلات
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// تأثيرات السحب والإفلات
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
    dropZone.classList.add('drag-over');
}

function unhighlight(e) {
    dropZone.classList.remove('drag-over');
}

// معالجة إسقاط الملف
dropZone.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// معالجة اختيار الملف
fileInput.addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// معالجة الملف المختار
function handleFile(file) {
    // التحقق من نوع الملف
    const validTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/json'];
    const validExtensions = ['.csv', '.xls', '.xlsx', '.json'];
    
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
        showAlert('نوع الملف غير مدعوم. الرجاء اختيار ملف CSV, Excel, أو JSON.', 'error');
        return;
    }
    
    // حفظ الملف وعرض معلوماته
    selectedFile = file;
    displayFileInfo(file);
    document.getElementById('previewBtn').disabled = false;
}

// عرض معلومات الملف
function displayFileInfo(file) {
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
    document.getElementById('fileType').textContent = file.type || 'غير محدد';
    document.getElementById('fileInfo').classList.remove('hidden');
}

// تنسيق حجم الملف
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// مسح الملف
function clearFile() {
    selectedFile = null;
    fileInput.value = '';
    document.getElementById('fileInfo').classList.add('hidden');
    document.getElementById('previewBtn').disabled = true;
}

// معاينة الاستيراد
async function previewImport() {
    if (!selectedFile) return;
    
    showLoading('جاري قراءة الملف...');
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
        const response = await fetch(`/${currentEntity}/import/preview`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        hideLoading();
        
        if (result.success) {
            previewData = result;
            displayPreview(result);
            showStep('preview');
        } else {
            showAlert(result.message || 'حدث خطأ في قراءة الملف', 'error');
        }
    } catch (error) {
        hideLoading();
        showAlert('حدث خطأ في الاتصال بالخادم', 'error');
    }
}

// عرض المعاينة
function displayPreview(data) {
    // عرض البيانات الوصفية
    const metadataHtml = `
        <div class="flex flex-wrap gap-4">
            <div>
                <span class="font-semibold">إجمالي السطور:</span> ${data.total_rows}
            </div>
            <div>
                <span class="font-semibold">سطور صحيحة:</span> ${data.valid_rows}
            </div>
            <div>
                <span class="font-semibold">أخطاء:</span> ${data.error_count}
            </div>
            ${data.encoding ? `<div><span class="font-semibold">الترميز:</span> ${data.encoding}</div>` : ''}
        </div>
    `;
    document.getElementById('importMetadata').innerHTML = metadataHtml;
    
    // عرض التحذيرات إن وجدت
    if (data.warnings && data.warnings.length > 0) {
        const warningsHtml = `
            <div class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <h5 class="font-semibold text-yellow-800 mb-2">
                    <i class="fas fa-exclamation-triangle ml-1"></i>
                    تحذيرات (${data.warnings.length})
                </h5>
                <ul class="text-sm text-yellow-700 list-disc list-inside">
                    ${data.warnings.map(w => `<li>${w}</li>`).join('')}
                </ul>
            </div>
        `;
        document.getElementById('importWarnings').innerHTML = warningsHtml;
        document.getElementById('importWarnings').classList.remove('hidden');
    }
    
    // عرض جدول المعاينة
    if (data.preview && data.preview.length > 0) {
        const headers = Object.keys(data.preview[0]);
        const tableHtml = `
            <thead class="bg-gray-50">
                <tr>
                    ${headers.map(h => `<th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">${h}</th>`).join('')}
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                ${data.preview.map((row, i) => `
                    <tr class="${data.row_errors && data.row_errors[i] ? 'import-error' : ''}">
                        ${headers.map(h => `<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${row[h] || '-'}</td>`).join('')}
                    </tr>
                `).join('')}
            </tbody>
        `;
        document.getElementById('previewTable').innerHTML = tableHtml;
    }
    
    // تفعيل/تعطيل زر الاستيراد
    document.getElementById('importBtn').disabled = data.valid_rows === 0;
}

// الرجوع لرفع الملف
function backToUpload() {
    showStep('upload');
    previewData = null;
}

// تأكيد الاستيراد
async function confirmImport() {
    if (!selectedFile || !previewData) return;
    
    showLoading('جاري استيراد البيانات...');
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('confirm', 'true');
    
    try {
        const response = await fetch(`/${currentEntity}/import`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        hideLoading();
        
        displayImportResults(result);
        showStep('result');
        
        if (result.success) {
            // تحديث الصفحة بعد 3 ثواني
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        }
    } catch (error) {
        hideLoading();
        showAlert('حدث خطأ في الاتصال بالخادم', 'error');
    }
}

// عرض نتائج الاستيراد
function displayImportResults(result) {
    let html = '';
    
    if (result.success) {
        html = `
            <div class="text-center py-8">
                <i class="fas fa-check-circle text-6xl text-green-500 mb-4"></i>
                <h3 class="text-2xl font-bold text-gray-900 mb-2">تم الاستيراد بنجاح!</h3>
                <div class="mt-4 space-y-2">
                    <p class="text-lg">
                        <span class="font-semibold">تم استيراد:</span> ${result.imported_count} سجل
                    </p>
                    ${result.skipped_count > 0 ? `
                        <p class="text-yellow-600">
                            <span class="font-semibold">تم تخطي:</span> ${result.skipped_count} سجل مكرر
                        </p>
                    ` : ''}
                    ${result.error_count > 0 ? `
                        <p class="text-red-600">
                            <span class="font-semibold">أخطاء:</span> ${result.error_count} سجل
                        </p>
                    ` : ''}
                </div>
            </div>
        `;
    } else {
        html = `
            <div class="text-center py-8">
                <i class="fas fa-times-circle text-6xl text-red-500 mb-4"></i>
                <h3 class="text-2xl font-bold text-gray-900 mb-2">فشل الاستيراد</h3>
                <p class="text-gray-600 mb-4">${result.message || 'حدث خطأ أثناء الاستيراد'}</p>
                ${result.errors && result.errors.length > 0 ? `
                    <div class="mt-4 text-right">
                        <h4 class="font-semibold text-red-800 mb-2">الأخطاء:</h4>
                        <ul class="text-sm text-red-600 list-disc list-inside max-h-40 overflow-y-auto">
                            ${result.errors.map(e => `<li>${e}</li>`).join('')}
                        </ul>
                        ${result.has_more_errors ? `
                            <p class="text-sm text-gray-500 mt-2">
                                ... و ${result.total_errors - result.errors.length} خطأ آخر
                            </p>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    document.getElementById('importResults').innerHTML = html;
}

// تصدير البيانات
async function exportData(format) {
    showLoading('جاري تحضير الملف...');
    
    const params = new URLSearchParams();
    
    // إضافة الخيارات
    if (format === 'excel' && document.getElementById('exportWithStats').checked) {
        params.append('with_stats', 'true');
    }
    
    if (document.getElementById('exportActive').checked) {
        params.append('status', 'active');
    }
    
    try {
        const response = await fetch(`/${currentEntity}/export/${format}?${params.toString()}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // اسم الملف من الاستجابة
            const contentDisposition = response.headers.get('Content-Disposition');
            const fileNameMatch = contentDisposition && contentDisposition.match(/filename="(.+)"/);
            const fileName = fileNameMatch ? fileNameMatch[1] : `export_${Date.now()}.${format}`;
            
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            hideLoading();
            showAlert('تم تحميل الملف بنجاح', 'success');
            
            setTimeout(() => {
                closeImportExportModal();
            }, 1500);
        } else {
            hideLoading();
            showAlert('حدث خطأ في تصدير البيانات', 'error');
        }
    } catch (error) {
        hideLoading();
        showAlert('حدث خطأ في الاتصال بالخادم', 'error');
    }
}

// تحميل نموذج فارغ
async function downloadTemplate(format) {
    const templates = {
        csv: 'data:text/csv;charset=utf-8,\ufeffالاسم,الهاتف,البريد الإلكتروني,الرقم القومي,العنوان,الحالة,الملاحظات\nأحمد محمد,01234567890,ahmad@email.com,12345678901234,القاهرة - مصر,نشط,عميل مميز',
        excel: '/static/templates/customers_template.xlsx',
        json: 'data:application/json;charset=utf-8,' + encodeURIComponent(JSON.stringify([{
            "الاسم": "أحمد محمد",
            "الهاتف": "01234567890",
            "البريد الإلكتروني": "ahmad@email.com",
            "الرقم القومي": "12345678901234",
            "العنوان": "القاهرة - مصر",
            "الحالة": "نشط",
            "الملاحظات": "عميل مميز"
        }], null, 2))
    };
    
    const a = document.createElement('a');
    a.href = templates[format];
    a.download = `نموذج_العملاء.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// عرض/إخفاء مؤشر التحميل
function showLoading(text = 'جاري المعالجة...') {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

// عرض رسالة تنبيه
function showAlert(message, type = 'info') {
    // يمكنك استبدال هذا بنظام toast أو أي نظام تنبيهات آخر
    alert(message);
}