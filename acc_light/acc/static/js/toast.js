// Toast Notification System
class ToastManager {
    constructor() {
        this.container = null;
        this.init();
    }

    init() {
        // Create container if it doesn't exist
        if (!document.querySelector('.toast-container')) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.querySelector('.toast-container');
        }
    }

    show(message, type = 'info', title = null, duration = 5000) {
        const toast = this.createToast(message, type, title, duration);
        this.container.appendChild(toast);
        
        // Trigger show animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.remove(toast);
            }, duration);
        }

        return toast;
    }

    createToast(message, type, title, duration) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        // Icons for different types
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        // Default titles if not provided
        const defaultTitles = {
            success: 'نجاح',
            error: 'خطأ',
            warning: 'تحذير',
            info: 'معلومة'
        };

        const toastTitle = title || defaultTitles[type] || '';
        
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">
                    <i class="fas ${icons[type] || 'fa-info-circle'}"></i>
                </div>
                <div class="toast-body">
                    ${toastTitle ? `<div class="toast-title">${toastTitle}</div>` : ''}
                    <div class="toast-message">${message}</div>
                </div>
                <button class="toast-close" onclick="toast.remove(this.closest('.toast'))">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            ${duration > 0 ? '<div class="toast-progress"></div>' : ''}
        `;

        return toast;
    }

    remove(toastElement) {
        toastElement.classList.remove('show');
        toastElement.classList.add('hide');
        
        setTimeout(() => {
            if (toastElement.parentNode) {
                toastElement.parentNode.removeChild(toastElement);
            }
        }, 300);
    }

    success(message, title = null, duration = 5000) {
        return this.show(message, 'success', title, duration);
    }

    error(message, title = null, duration = 7000) {
        return this.show(message, 'error', title, duration);
    }

    warning(message, title = null, duration = 6000) {
        return this.show(message, 'warning', title, duration);
    }

    info(message, title = null, duration = 5000) {
        return this.show(message, 'info', title, duration);
    }

    // Show loading toast (no auto-dismiss)
    loading(message, title = 'جاري المعالجة...') {
        const toast = this.show(message, 'info', title, 0);
        toast.querySelector('.toast-icon i').className = 'fas fa-spinner fa-spin';
        return toast;
    }

    // Clear all toasts
    clear() {
        const toasts = this.container.querySelectorAll('.toast');
        toasts.forEach(toast => this.remove(toast));
    }
}

// Create global instance
window.toast = new ToastManager();

// Helper function to handle form submissions with loading state
function handleFormSubmit(form, loadingMessage = 'جاري الحفظ...') {
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    
    // Show loading state
    submitButton.classList.add('btn-loading');
    submitButton.disabled = true;
    
    const loadingToast = toast.loading(loadingMessage);
    
    // Return cleanup function
    return function cleanup(success = true, message = null) {
        // Remove loading toast
        toast.remove(loadingToast);
        
        // Reset button
        submitButton.classList.remove('btn-loading');
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
        
        // Show result message if provided
        if (message) {
            if (success) {
                toast.success(message);
            } else {
                toast.error(message);
            }
        }
    };
}

// Convert Flask flash messages to toasts
document.addEventListener('DOMContentLoaded', function() {
    // Look for flash messages in the page
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        const type = msg.dataset.type || 'info';
        const message = msg.textContent.trim();
        
        // Map Flask message types to our toast types
        const typeMap = {
            'success': 'success',
            'error': 'error',
            'danger': 'error',
            'warning': 'warning',
            'info': 'info'
        };
        
        toast.show(message, typeMap[type] || 'info');
        
        // Remove the original flash message
        msg.remove();
    });
});