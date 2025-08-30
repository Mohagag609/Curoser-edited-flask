// Enhanced Toast System - Faster and No Duplicates
class EnhancedToastManager {
    constructor() {
        this.container = null;
        this.activeToasts = new Map(); // Track active toasts to prevent duplicates
        this.queue = [];
        this.maxVisible = 3;
        this.init();
    }

    init() {
        // Create container with fixed positioning
        this.container = document.getElementById('toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.style.cssText = `
                position: fixed;
                top: 20px;
                left: 20px;
                z-index: 9999;
                pointer-events: none;
            `;
            document.body.appendChild(this.container);
        }
    }

    show(message, type = 'info', duration = 3000) {
        // Create unique key for message
        const key = `${type}:${message}`;
        
        // Check if already showing
        if (this.activeToasts.has(key)) {
            return;
        }

        // Create toast element
        const toast = document.createElement('div');
        toast.style.cssText = `
            background: white;
            color: #333;
            padding: 12px 20px;
            margin-bottom: 10px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 300px;
            max-width: 500px;
            pointer-events: all;
            cursor: pointer;
            transition: all 0.2s ease;
            transform: translateX(-400px);
            opacity: 0;
            border-right: 4px solid;
        `;

        // Colors based on type
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };

        toast.style.borderRightColor = colors[type] || colors.info;

        // Icon
        const icons = {
            success: '✓',
            error: '✕',
            warning: '!',
            info: 'i'
        };

        const iconSpan = document.createElement('span');
        iconSpan.style.cssText = `
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: ${colors[type] || colors.info};
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            flex-shrink: 0;
        `;
        iconSpan.textContent = icons[type] || icons.info;

        // Message
        const messageSpan = document.createElement('span');
        messageSpan.style.cssText = `
            flex: 1;
            font-size: 14px;
            line-height: 1.4;
        `;
        messageSpan.textContent = message;

        // Close button
        const closeBtn = document.createElement('button');
        closeBtn.style.cssText = `
            background: none;
            border: none;
            padding: 4px;
            cursor: pointer;
            color: #999;
            font-size: 18px;
            line-height: 1;
            transition: color 0.2s;
        `;
        closeBtn.innerHTML = '×';
        closeBtn.onmouseover = () => closeBtn.style.color = '#333';
        closeBtn.onmouseout = () => closeBtn.style.color = '#999';
        closeBtn.onclick = (e) => {
            e.stopPropagation();
            this.remove(toast, key);
        };

        // Assemble toast
        toast.appendChild(iconSpan);
        toast.appendChild(messageSpan);
        toast.appendChild(closeBtn);

        // Click to dismiss
        toast.onclick = () => this.remove(toast, key);

        // Add to container
        this.container.appendChild(toast);
        this.activeToasts.set(key, toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0)';
            toast.style.opacity = '1';
        });

        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                this.remove(toast, key);
            }, duration);
        }

        // Remove old toasts if too many
        if (this.activeToasts.size > this.maxVisible) {
            const oldestKey = this.activeToasts.keys().next().value;
            const oldestToast = this.activeToasts.get(oldestKey);
            this.remove(oldestToast, oldestKey);
        }
    }

    remove(toast, key) {
        if (!toast) return;
        
        // Animate out
        toast.style.transform = 'translateX(-400px)';
        toast.style.opacity = '0';
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            this.activeToasts.delete(key);
        }, 200);
    }

    success(message) {
        this.show(message, 'success');
    }

    error(message) {
        this.show(message, 'error');
    }

    warning(message) {
        this.show(message, 'warning');
    }

    info(message) {
        this.show(message, 'info');
    }

    loading(message) {
        const key = `loading:${message}`;
        
        if (this.activeToasts.has(key)) {
            return this.activeToasts.get(key);
        }

        const toast = document.createElement('div');
        toast.style.cssText = `
            background: white;
            color: #333;
            padding: 12px 20px;
            margin-bottom: 10px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 300px;
            pointer-events: none;
            transition: all 0.2s ease;
            transform: translateX(-400px);
            opacity: 0;
        `;

        // Spinner
        const spinner = document.createElement('div');
        spinner.style.cssText = `
            width: 20px;
            height: 20px;
            border: 2px solid #e5e7eb;
            border-top-color: #3b82f6;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        `;

        // Message
        const messageSpan = document.createElement('span');
        messageSpan.textContent = message;

        toast.appendChild(spinner);
        toast.appendChild(messageSpan);

        this.container.appendChild(toast);
        this.activeToasts.set(key, toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0)';
            toast.style.opacity = '1';
        });

        return toast;
    }

    clear() {
        this.activeToasts.forEach((toast, key) => {
            this.remove(toast, key);
        });
    }
}

// Add spinner animation
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// Create global instance
window.toast = new EnhancedToastManager();