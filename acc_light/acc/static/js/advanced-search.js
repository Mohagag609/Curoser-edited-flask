/**
 * Advanced Search System
 * نظام بحث متقدم مع دعم البحث الفوري والفلترة المتقدمة
 */

class AdvancedSearch {
    constructor(options) {
        this.searchInput = document.querySelector(options.searchInput || '#search-input');
        this.resultsContainer = document.querySelector(options.resultsContainer || '#results-container');
        this.searchUrl = options.searchUrl;
        this.minChars = options.minChars || 2;
        this.delay = options.delay || 300;
        this.fields = options.fields || [];
        
        this.searchTimeout = null;
        this.currentRequest = null;
        
        this.init();
    }
    
    init() {
        if (!this.searchInput) return;
        
        // Live search on input
        this.searchInput.addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });
        
        // Search on Enter
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performSearch(e.target.value);
            }
        });
        
        // Clear button
        const clearBtn = this.searchInput.parentElement.querySelector('.search-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.searchInput.value = '';
                this.handleSearch('');
            });
        }
    }
    
    handleSearch(query) {
        // Clear previous timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Show/hide clear button
        const clearBtn = this.searchInput.parentElement.querySelector('.search-clear');
        if (clearBtn) {
            clearBtn.style.display = query ? 'block' : 'none';
        }
        
        // Minimum characters check
        if (query.length > 0 && query.length < this.minChars) {
            this.showMessage(`أدخل ${this.minChars} أحرف على الأقل للبحث`);
            return;
        }
        
        // Debounce search
        this.searchTimeout = setTimeout(() => {
            this.performSearch(query);
        }, this.delay);
    }
    
    async performSearch(query) {
        // Cancel previous request
        if (this.currentRequest && this.currentRequest.abort) {
            this.currentRequest.abort();
        }
        
        // Show loading
        this.showLoading();
        
        try {
            // Create controller for cancellation
            const controller = new AbortController();
            this.currentRequest = controller;
            
            // Build search URL
            const url = new URL(this.searchUrl, window.location.origin);
            url.searchParams.set('q', query);
            
            // Add any active filters
            const filters = this.getActiveFilters();
            Object.keys(filters).forEach(key => {
                url.searchParams.set(key, filters[key]);
            });
            
            // Perform search
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'text/html'
                },
                signal: controller.signal
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const html = await response.text();
            
            // Update results
            if (this.resultsContainer) {
                this.resultsContainer.innerHTML = html;
                
                // Re-initialize any JavaScript components
                this.initializeComponents();
            }
            
        } catch (error) {
            if (error.name !== 'AbortError') {
                this.showError('حدث خطأ في البحث. الرجاء المحاولة مرة أخرى.');
                console.error('Search error:', error);
            }
        } finally {
            this.currentRequest = null;
        }
    }
    
    getActiveFilters() {
        const filters = {};
        
        // Get all filter inputs
        document.querySelectorAll('[data-filter]').forEach(element => {
            const filterName = element.dataset.filter;
            let value;
            
            if (element.type === 'checkbox') {
                value = element.checked ? element.value : '';
            } else if (element.type === 'radio') {
                if (element.checked) {
                    value = element.value;
                }
            } else {
                value = element.value;
            }
            
            if (value) {
                filters[filterName] = value;
            }
        });
        
        return filters;
    }
    
    showLoading() {
        if (!this.resultsContainer) return;
        
        this.resultsContainer.innerHTML = `
            <div class="flex justify-center items-center py-12">
                <div class="text-center">
                    <div class="inline-flex items-center gap-3">
                        <svg class="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span class="text-lg text-gray-600">جاري البحث...</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    showMessage(message) {
        if (!this.resultsContainer) return;
        
        this.resultsContainer.innerHTML = `
            <div class="flex justify-center items-center py-12">
                <div class="text-center">
                    <i class="fas fa-info-circle text-4xl text-gray-400 mb-3"></i>
                    <p class="text-gray-600">${message}</p>
                </div>
            </div>
        `;
    }
    
    showError(message) {
        if (!this.resultsContainer) return;
        
        this.resultsContainer.innerHTML = `
            <div class="flex justify-center items-center py-12">
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle text-4xl text-red-400 mb-3"></i>
                    <p class="text-red-600">${message}</p>
                </div>
            </div>
        `;
    }
    
    initializeComponents() {
        // Re-initialize delete buttons
        document.querySelectorAll('[data-confirm-delete]').forEach(btn => {
            // Event listeners are delegated, so no need to re-attach
        });
        
        // Re-initialize tooltips if any
        if (typeof tippy !== 'undefined') {
            tippy('[data-tippy-content]');
        }
        
        // Trigger custom event
        document.dispatchEvent(new CustomEvent('search:updated', {
            detail: { container: this.resultsContainer }
        }));
    }
}

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize for any element with data-advanced-search
    document.querySelectorAll('[data-advanced-search]').forEach(element => {
        const options = {
            searchInput: element.dataset.searchInput || '#' + element.id,
            resultsContainer: element.dataset.resultsContainer,
            searchUrl: element.dataset.searchUrl,
            minChars: parseInt(element.dataset.minChars) || 2,
            delay: parseInt(element.dataset.delay) || 300
        };
        
        new AdvancedSearch(options);
    });
});