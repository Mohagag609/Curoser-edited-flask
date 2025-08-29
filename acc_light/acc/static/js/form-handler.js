// Enhanced Form Handler with Toast Notifications
document.addEventListener('DOMContentLoaded', function() {
    // Handle all forms with data-ajax attribute
    const ajaxForms = document.querySelectorAll('form[data-ajax="true"]');
    
    ajaxForms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            const loadingMessage = form.dataset.loadingMessage || 'جاري المعالجة...';
            const successMessage = form.dataset.successMessage || 'تمت العملية بنجاح';
            const errorMessage = form.dataset.errorMessage || 'حدث خطأ أثناء المعالجة';
            
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.classList.add('btn-loading');
            const loadingToast = toast.loading(loadingMessage);
            
            try {
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: form.method || 'POST',
                    body: formData
                });
                
                // Remove loading toast
                toast.remove(loadingToast);
                
                if (response.ok) {
                    const contentType = response.headers.get("content-type");
                    
                    if (contentType && contentType.indexOf("application/json") !== -1) {
                        // Handle JSON response
                        const data = await response.json();
                        
                        if (data.success) {
                            toast.success(data.message || successMessage);
                            
                            // Redirect if URL provided
                            if (data.redirect) {
                                setTimeout(() => {
                                    window.location.href = data.redirect;
                                }, 1500);
                            }
                            
                            // Reset form if specified
                            if (form.dataset.resetOnSuccess === 'true') {
                                form.reset();
                            }
                        } else {
                            toast.error(data.message || errorMessage);
                        }
                    } else {
                        // Handle HTML response (redirect)
                        if (response.redirected) {
                            toast.success(successMessage);
                            setTimeout(() => {
                                window.location.href = response.url;
                            }, 1000);
                        } else {
                            // Parse HTML for flash messages
                            const text = await response.text();
                            const parser = new DOMParser();
                            const doc = parser.parseFromString(text, 'text/html');
                            
                            // Look for flash messages in the response
                            const flashMessages = doc.querySelectorAll('.flash-message');
                            if (flashMessages.length > 0) {
                                flashMessages.forEach(msg => {
                                    const type = msg.dataset.type || 'info';
                                    const message = msg.textContent.trim();
                                    
                                    if (type === 'error') {
                                        toast.error(message);
                                    } else if (type === 'success') {
                                        toast.success(message);
                                    } else if (type === 'warning') {
                                        toast.warning(message);
                                    } else {
                                        toast.info(message);
                                    }
                                });
                            } else {
                                toast.success(successMessage);
                            }
                        }
                    }
                } else {
                    // Handle error response
                    const contentType = response.headers.get("content-type");
                    
                    if (contentType && contentType.indexOf("application/json") !== -1) {
                        const data = await response.json();
                        toast.error(data.message || errorMessage);
                        
                        // Show field errors if any
                        if (data.errors) {
                            Object.keys(data.errors).forEach(field => {
                                const fieldElement = form.querySelector(`[name="${field}"]`);
                                if (fieldElement) {
                                    fieldElement.classList.add('border-red-500');
                                    const errorDiv = document.createElement('div');
                                    errorDiv.className = 'text-red-500 text-sm mt-1';
                                    errorDiv.textContent = data.errors[field];
                                    fieldElement.parentNode.appendChild(errorDiv);
                                }
                            });
                        }
                    } else {
                        toast.error(`خطأ: ${response.status} - ${response.statusText}`);
                    }
                }
            } catch (error) {
                // Remove loading toast
                toast.remove(loadingToast);
                toast.error(`خطأ في الاتصال: ${error.message}`);
            } finally {
                // Reset button state
                submitBtn.disabled = false;
                submitBtn.classList.remove('btn-loading');
                submitBtn.innerHTML = originalBtnText;
            }
        });
    });
    
    // Handle delete buttons with confirmation
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-confirm-delete]')) {
            e.preventDefault();
            
            const message = e.target.dataset.confirmMessage || 'هل أنت متأكد من الحذف؟';
            const deleteUrl = e.target.dataset.deleteUrl || e.target.href;
            
            if (confirm(message)) {
                const loadingToast = toast.loading('جاري الحذف...');
                
                fetch(deleteUrl, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    toast.remove(loadingToast);
                    
                    if (response.ok) {
                        toast.success('تم الحذف بنجاح');
                        
                        // Remove element from DOM if specified
                        const removeElement = e.target.dataset.removeElement;
                        if (removeElement) {
                            const element = e.target.closest(removeElement);
                            if (element) {
                                element.style.transition = 'opacity 0.3s';
                                element.style.opacity = '0';
                                setTimeout(() => element.remove(), 300);
                            }
                        } else {
                            // Reload page after delay
                            setTimeout(() => location.reload(), 1500);
                        }
                    } else {
                        response.text().then(text => {
                            toast.error(text || 'فشل الحذف');
                        });
                    }
                })
                .catch(error => {
                    toast.remove(loadingToast);
                    toast.error(`خطأ: ${error.message}`);
                });
            }
        }
    });
    
    // Auto-hide success messages after 5 seconds
    setTimeout(() => {
        const successToasts = document.querySelectorAll('.toast-success');
        successToasts.forEach(toast => {
            if (!toast.classList.contains('hide')) {
                window.toast.remove(toast);
            }
        });
    }, 5000);
});