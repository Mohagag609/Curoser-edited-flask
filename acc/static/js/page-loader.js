// Page Loader - Handles smooth transitions between pages
(function() {
    'use strict';
    
    // Create loading overlay
    function createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <div class="loading-text">جاري التحميل...</div>
                <div class="loading-progress">
                    <div class="loading-progress-bar"></div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        return overlay;
    }
    
    // Get or create overlay
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = createLoadingOverlay();
    }
    
    // Show loading
    function showLoading() {
        document.body.classList.add('transitioning');
        overlay.classList.add('active');
    }
    
    // Hide loading
    function hideLoading() {
        overlay.classList.remove('active');
        document.body.classList.remove('transitioning');
    }
    
    // Handle page load
    document.addEventListener('DOMContentLoaded', function() {
        // Hide loading on page load
        setTimeout(hideLoading, 300);
        
        // Intercept all navigation
        interceptNavigation();
    });
    
    // Intercept navigation
    function interceptNavigation() {
        // Handle link clicks
        document.addEventListener('click', function(e) {
            const link = e.target.closest('a');
            if (!link) return;
            
            // Skip special cases
            if (
                link.target === '_blank' ||
                link.href.startsWith('#') ||
                link.href.startsWith('javascript:') ||
                link.dataset.noLoader ||
                link.hasAttribute('download') ||
                link.hostname !== window.location.hostname ||
                link.classList.contains('no-loader')
            ) {
                return;
            }
            
            // Skip AJAX/HTMX links
            if (
                link.dataset.ajax === 'true' ||
                link.hasAttribute('hx-get') ||
                link.hasAttribute('hx-post') ||
                link.hasAttribute('hx-put') ||
                link.hasAttribute('hx-delete') ||
                link.hasAttribute('data-confirm-delete')
            ) {
                return;
            }
            
            // Show loading and navigate
            e.preventDefault();
            showLoading();
            
            // Small delay for animation
            setTimeout(() => {
                window.location.href = link.href;
            }, 300);
        });
        
        // Handle form submissions
        document.addEventListener('submit', function(e) {
            const form = e.target;
            
            // Skip AJAX forms
            if (form.dataset.ajax === 'true' || form.classList.contains('no-loader')) {
                return;
            }
            
            // Show loading
            showLoading();
        });
        
        // Handle browser back/forward
        window.addEventListener('pageshow', function(event) {
            if (event.persisted) {
                hideLoading();
            }
        });
        
        // Hide loading on unload (for back button)
        window.addEventListener('pagehide', function() {
            hideLoading();
        });
    }
    
    // Ensure loading is hidden on errors
    window.addEventListener('error', function() {
        hideLoading();
    });
    
    // Export for manual control
    window.pageLoader = {
        show: showLoading,
        hide: hideLoading
    };
})();