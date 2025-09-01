// Main JavaScript for Real Estate System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Confirm delete actions
    document.querySelectorAll('form[onsubmit*="confirm"]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm('هل أنت متأكد من هذا الإجراء؟')) {
                e.preventDefault();
            }
        });
    });

    // Format currency inputs
    document.querySelectorAll('input[type="number"][step="0.01"]').forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });

    // Auto-generate codes
    document.querySelectorAll('input[name="code"]').forEach(function(input) {
        var nameInput = input.closest('form').querySelector('input[name="name"]');
        if (nameInput) {
            nameInput.addEventListener('input', function() {
                if (!input.value) {
                    var code = generateCode(this.value);
                    input.value = code;
                }
            });
        }
    });

    // Search functionality
    var searchInputs = document.querySelectorAll('input[type="search"], input[name="search"]');
    searchInputs.forEach(function(input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                this.closest('form').submit();
            }
        });
    });

    // Table row selection
    document.querySelectorAll('table tbody tr').forEach(function(row) {
        row.addEventListener('click', function() {
            this.classList.toggle('table-active');
        });
    });

    // Form validation
    document.querySelectorAll('form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var requiredFields = form.querySelectorAll('[required]');
            var isValid = true;
            
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showAlert('يرجى ملء جميع الحقول المطلوبة', 'danger');
            }
        });
    });

    // Dynamic form fields
    document.querySelectorAll('[data-add-field]').forEach(function(button) {
        button.addEventListener('click', function() {
            var template = document.querySelector(this.dataset.addField);
            var container = document.querySelector(this.dataset.target);
            var clone = template.content.cloneNode(true);
            container.appendChild(clone);
        });
    });

    // Remove dynamic fields
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-remove-field]')) {
            e.target.closest('.dynamic-field').remove();
        }
    });

    // Date picker enhancements
    document.querySelectorAll('input[type="date"]').forEach(function(input) {
        input.addEventListener('change', function() {
            var startDate = this;
            var endDate = document.querySelector('input[name="expected_end_date"]');
            
            if (endDate && startDate.value) {
                endDate.min = startDate.value;
            }
        });
    });

    // Number formatting
    document.querySelectorAll('input[type="number"]').forEach(function(input) {
        input.addEventListener('input', function() {
            if (this.value && !isNaN(this.value)) {
                this.value = parseFloat(this.value);
            }
        });
    });

    // Copy to clipboard
    document.querySelectorAll('[data-copy]').forEach(function(button) {
        button.addEventListener('click', function() {
            var text = this.dataset.copy;
            navigator.clipboard.writeText(text).then(function() {
                showAlert('تم نسخ النص', 'success');
            });
        });
    });

    // Print functionality
    document.querySelectorAll('[data-print]').forEach(function(button) {
        button.addEventListener('click', function() {
            var target = document.querySelector(this.dataset.print);
            if (target) {
                printElement(target);
            } else {
                window.print();
            }
        });
    });

    // Export functionality
    document.querySelectorAll('[data-export]').forEach(function(button) {
        button.addEventListener('click', function() {
            var format = this.dataset.export;
            var table = this.closest('.card').querySelector('table');
            if (table) {
                exportTable(table, format);
            }
        });
    });
});

// Utility Functions
function generateCode(name) {
    if (!name) return '';
    var code = name.replace(/[^a-zA-Z0-9\u0600-\u06FF]/g, '').substring(0, 3).toUpperCase();
    var random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    return code + random;
}

function showAlert(message, type) {
    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alertDiv.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    
    var container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('ar-SA', {
        style: 'currency',
        currency: 'SAR'
    }).format(amount);
}

function printElement(element) {
    var printWindow = window.open('', '_blank');
    printWindow.document.write('<html><head><title>طباعة</title>');
    printWindow.document.write('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">');
    printWindow.document.write('<style>body{direction:rtl;text-align:right;}</style>');
    printWindow.document.write('</head><body>');
    printWindow.document.write(element.outerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

function exportTable(table, format) {
    if (format === 'csv') {
        exportToCSV(table);
    } else if (format === 'excel') {
        exportToExcel(table);
    }
}

function exportToCSV(table) {
    var csv = [];
    var rows = table.querySelectorAll('tr');
    
    for (var i = 0; i < rows.length; i++) {
        var row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (var j = 0; j < cols.length; j++) {
            row.push(cols[j].innerText);
        }
        
        csv.push(row.join(','));
    }
    
    var csvContent = csv.join('\n');
    var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    var link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'export.csv';
    link.click();
}

function exportToExcel(table) {
    var wb = XLSX.utils.table_to_book(table);
    XLSX.writeFile(wb, 'export.xlsx');
}

// AJAX Functions
function ajaxRequest(url, method, data, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                callback(null, response);
            } else {
                callback(new Error('Request failed'), null);
            }
        }
    };
    
    xhr.send(JSON.stringify(data));
}

// Form Helpers
function resetForm(form) {
    form.reset();
    form.querySelectorAll('.is-invalid').forEach(function(field) {
        field.classList.remove('is-invalid');
    });
}

function validateForm(form) {
    var isValid = true;
    var requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Date Helpers
function formatDate(date) {
    return new Intl.DateTimeFormat('ar-SA').format(new Date(date));
}

function getCurrentDate() {
    var today = new Date();
    var year = today.getFullYear();
    var month = String(today.getMonth() + 1).padStart(2, '0');
    var day = String(today.getDate()).padStart(2, '0');
    return year + '-' + month + '-' + day;
}

// Number Helpers
function formatNumber(number) {
    return new Intl.NumberFormat('ar-SA').format(number);
}

function parseNumber(str) {
    return parseFloat(str.replace(/[^\d.-]/g, ''));
}

// Local Storage Helpers
function saveToStorage(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

function loadFromStorage(key) {
    var item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;
}

// Debounce Function
function debounce(func, wait) {
    var timeout;
    return function executedFunction() {
        var later = function() {
            clearTimeout(timeout);
            func();
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle Function
function throttle(func, limit) {
    var inThrottle;
    return function() {
        var args = arguments;
        var context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(function() {
                inThrottle = false;
            }, limit);
        }
    };
}