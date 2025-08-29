// Dark Mode Manager
class DarkMode {
    constructor() {
        this.isDark = localStorage.getItem('darkMode') === 'true';
        this.init();
    }

    init() {
        // تطبيق الوضع المحفوظ
        this.apply();
        
        // إضافة زر التبديل
        this.createToggle();
    }

    createToggle() {
        // البحث عن مكان مناسب لوضع الزر
        const nav = document.querySelector('nav');
        if (!nav) return;

        const toggle = document.createElement('button');
        toggle.id = 'dark-mode-toggle';
        toggle.className = 'p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors';
        toggle.innerHTML = this.isDark ? 
            '<i class="fas fa-sun text-yellow-500"></i>' : 
            '<i class="fas fa-moon text-gray-600"></i>';
        
        toggle.addEventListener('click', () => this.toggle());
        
        // إضافة الزر للشريط العلوي
        const navEnd = nav.querySelector('.flex.items-center.space-x-reverse');
        if (navEnd) {
            navEnd.insertBefore(toggle, navEnd.firstChild);
        }
    }

    toggle() {
        this.isDark = !this.isDark;
        localStorage.setItem('darkMode', this.isDark);
        this.apply();
        this.updateToggleIcon();
    }

    apply() {
        if (this.isDark) {
            document.documentElement.classList.add('dark');
            // تطبيق الألوان الداكنة
            this.applyDarkStyles();
        } else {
            document.documentElement.classList.remove('dark');
            // إزالة الألوان الداكنة
            this.removeDarkStyles();
        }
    }

    applyDarkStyles() {
        // إضافة أنماط CSS للوضع الليلي
        if (!document.getElementById('dark-mode-styles')) {
            const style = document.createElement('style');
            style.id = 'dark-mode-styles';
            style.textContent = `
                .dark body {
                    background-color: #0f172a;
                    color: #e2e8f0;
                }
                
                .dark .bg-white {
                    background-color: #1e293b;
                }
                
                .dark .bg-gray-50 {
                    background-color: #0f172a;
                }
                
                .dark .text-gray-900 {
                    color: #f1f5f9;
                }
                
                .dark .text-gray-700 {
                    color: #cbd5e1;
                }
                
                .dark .text-gray-600 {
                    color: #94a3b8;
                }
                
                .dark .text-gray-500 {
                    color: #64748b;
                }
                
                .dark .border-gray-200 {
                    border-color: #334155;
                }
                
                .dark .border-gray-300 {
                    border-color: #475569;
                }
                
                .dark .hover\\:bg-gray-50:hover {
                    background-color: #334155;
                }
                
                .dark .hover\\:bg-gray-100:hover {
                    background-color: #475569;
                }
                
                .dark .card {
                    background-color: #1e293b;
                    border-color: #334155;
                }
                
                .dark .form-input,
                .dark .form-select {
                    background-color: #0f172a;
                    border-color: #334155;
                    color: #e2e8f0;
                }
                
                .dark .form-input:focus,
                .dark .form-select:focus {
                    border-color: #3b82f6;
                }
                
                .dark .table {
                    background-color: #1e293b;
                }
                
                .dark .table thead {
                    background-color: #0f172a;
                }
                
                .dark .table tbody tr {
                    border-color: #334155;
                }
                
                .dark .table tbody tr:hover {
                    background-color: #334155;
                }
            `;
            document.head.appendChild(style);
        }
    }

    removeDarkStyles() {
        const style = document.getElementById('dark-mode-styles');
        if (style) {
            style.remove();
        }
    }

    updateToggleIcon() {
        const toggle = document.getElementById('dark-mode-toggle');
        if (toggle) {
            toggle.innerHTML = this.isDark ? 
                '<i class="fas fa-sun text-yellow-500"></i>' : 
                '<i class="fas fa-moon text-gray-600"></i>';
        }
    }
}

// تهيئة Dark Mode
document.addEventListener('DOMContentLoaded', () => {
    new DarkMode();
});