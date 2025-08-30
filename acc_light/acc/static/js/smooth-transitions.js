// Smooth Page Transitions - Simplified Version
(function() {
    'use strict';
    
    // Add smooth transition class to body
    document.addEventListener('DOMContentLoaded', function() {
        document.body.classList.add('page-loaded');
        
        // Animate elements on page load
        animatePageElements();
        
        // Handle link clicks for smooth transitions
        handleSmoothNavigation();
    });
    
    // Animate page elements
    function animatePageElements() {
        // Add stagger class to lists
        const lists = document.querySelectorAll('tbody, .grid');
        lists.forEach(list => {
            list.classList.add('stagger-list');
        });
        
        // Add will-change to animated elements
        const animatedElements = document.querySelectorAll('.card, .modern-btn, .sidebar');
        animatedElements.forEach(el => {
            el.classList.add('will-change-transform');
        });
    }
    
    // Handle smooth navigation
    function handleSmoothNavigation() {
        // Intercept non-AJAX links
        document.addEventListener('click', function(e) {
            const link = e.target.closest('a');
            if (!link) return;
            
            // Skip special cases
            if (
                link.target === '_blank' ||
                link.href.startsWith('#') ||
                link.dataset.noTransition ||
                link.hasAttribute('download') ||
                link.hostname !== window.location.hostname ||
                link.dataset.ajax === 'true' ||
                link.hasAttribute('hx-get') ||
                link.hasAttribute('hx-post')
            ) {
                return;
            }
            
            // Add exit animation
            e.preventDefault();
            document.body.style.opacity = '0.8';
            
            setTimeout(() => {
                window.location.href = link.href;
            }, 200);
        });
    }
    
    // Handle browser back/forward
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            document.body.style.opacity = '1';
            animatePageElements();
        }
    });
    
    // Ensure forms don't cause jarring transitions
    document.addEventListener('submit', function(e) {
        const form = e.target;
        
        // Skip AJAX forms
        if (form.dataset.ajax === 'true') return;
        
        // Add subtle fade
        document.body.style.opacity = '0.9';
    });
})();