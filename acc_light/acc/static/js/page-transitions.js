// Page Transitions Handler
(function() {
    'use strict';
    
    // Create loading overlay
    const createLoadingOverlay = () => {
        const overlay = document.createElement('div');
        overlay.className = 'page-loading-overlay';
        overlay.innerHTML = `
            <div class="text-center">
                <div class="loading-spinner mx-auto mb-4"></div>
                <p class="text-gray-600 text-sm">جاري التحميل...</p>
            </div>
        `;
        document.body.appendChild(overlay);
        return overlay;
    };
    
    // Get or create loading overlay
    let loadingOverlay = document.querySelector('.page-loading-overlay');
    if (!loadingOverlay) {
        loadingOverlay = createLoadingOverlay();
    }
    
    // Show loading overlay
    const showLoading = () => {
        loadingOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    };
    
    // Hide loading overlay
    const hideLoading = () => {
        loadingOverlay.classList.remove('active');
        document.body.style.overflow = '';
    };
    
    // Initialize page
    const initializePage = () => {
        // Mark body as loaded
        document.body.classList.add('page-loaded');
        
        // Fade in page content
        const pageContent = document.querySelector('.page-content');
        if (pageContent) {
            setTimeout(() => {
                pageContent.classList.add('loaded');
            }, 100);
        }
        
        // Animate cards
        const cards = document.querySelectorAll('.card-transition');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('visible');
            }, 100 + (index * 50));
        });
        
        // Animate list items
        const listItems = document.querySelectorAll('.stagger-item');
        listItems.forEach((item, index) => {
            setTimeout(() => {
                item.classList.add('visible');
            }, 100 + (index * 30));
        });
        
        // Hide loading overlay
        hideLoading();
    };
    
    // Handle page navigation
    const handleNavigation = (url) => {
        showLoading();
        
        // Add slight delay for smooth transition
        setTimeout(() => {
            window.location.href = url;
        }, 300);
    };
    
    // Intercept navigation links
    const interceptLinks = () => {
        // Regular links
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (!link) return;
            
            // Skip if:
            // - Has target="_blank"
            // - Is a hash link
            // - Has data-no-transition
            // - Is a download link
            // - Is an external link
            // - Has onclick handler
            if (
                link.target === '_blank' ||
                link.href.startsWith('#') ||
                link.dataset.noTransition ||
                link.hasAttribute('download') ||
                link.hostname !== window.location.hostname ||
                link.onclick ||
                link.classList.contains('btn-delete') ||
                link.dataset.confirmDelete
            ) {
                return;
            }
            
            // Skip HTMX links
            if (link.hasAttribute('hx-get') || 
                link.hasAttribute('hx-post') || 
                link.hasAttribute('hx-put') || 
                link.hasAttribute('hx-delete')) {
                return;
            }
            
            e.preventDefault();
            handleNavigation(link.href);
        });
        
        // Form submissions (non-AJAX)
        document.addEventListener('submit', (e) => {
            const form = e.target;
            
            // Skip if:
            // - Has data-ajax="true"
            // - Has data-no-transition
            if (form.dataset.ajax === 'true' || form.dataset.noTransition) {
                return;
            }
            
            showLoading();
        });
    };
    
    // Handle browser back/forward
    window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
            hideLoading();
            initializePage();
        }
    });
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            interceptLinks();
            initializePage();
        });
    } else {
        interceptLinks();
        initializePage();
    }
    
    // Hide loading on page unload (for back button)
    window.addEventListener('pagehide', () => {
        hideLoading();
    });
    
    // Export functions for manual use
    window.pageTransitions = {
        showLoading,
        hideLoading,
        handleNavigation
    };
})();