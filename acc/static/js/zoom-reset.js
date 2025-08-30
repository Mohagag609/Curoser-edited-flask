// Reset zoom on page load and navigation
(function() {
    'use strict';
    
    // Reset zoom function
    function resetZoom() {
        // Reset viewport
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
        }
        
        // Force browser to reset zoom
        document.body.style.zoom = '1';
        document.documentElement.style.zoom = '1';
        
        // Reset any CSS transforms
        document.body.style.transform = 'none';
        document.body.style.webkitTransform = 'none';
        
        // Force reflow
        void document.body.offsetHeight;
        
        // Reset scroll position
        window.scrollTo(0, 0);
    }
    
    // Reset on page load
    window.addEventListener('load', resetZoom);
    
    // Reset on page show (for back/forward navigation)
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            resetZoom();
        }
    });
    
    // Reset after project switch
    document.addEventListener('DOMContentLoaded', function() {
        // Check if we just switched projects
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('project_switched') === 'true') {
            resetZoom();
            // Remove the parameter from URL
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    });
    
    // Prevent pinch zoom on mobile
    document.addEventListener('touchstart', function(event) {
        if (event.touches.length > 1) {
            event.preventDefault();
        }
    }, { passive: false });
    
    // Handle orientation change
    window.addEventListener('orientationchange', function() {
        setTimeout(resetZoom, 100);
    });
    
    // Export for manual use
    window.resetZoom = resetZoom;
})();