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
        // Page loader handles navigation now
        // Just ensure animations work on page load
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