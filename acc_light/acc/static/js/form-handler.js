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
            
            // Show loading state only if not disabled
            let loadingToast = null;
            if (!form.dataset.noLoading) {
                submitBtn.disabled = true;
                submitBtn.classList.add('btn-loading');
                loadingToast = toast.loading(loadingMessage);
            }
            
            try {
                const formData = new FormData(form);
                const response = await fetch(form.action, {
                    method: form.method || 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                // Remove loading toast if it exists
                if (loadingToast) {
                    toast.remove(loadingToast);
                }
                
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
                            
                            // If redirect URL provided for duplicate entry
                            if (data.duplicate && data.redirect) {
                                setTimeout(() => {
                                    if (confirm('هل تريد الانتقال إلى السجل الموجود؟')) {
                                        window.location.href = data.redirect;
                                    }
                                }, 1500);
                            }
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
                // Remove loading toast if it exists
                if (loadingToast) {
                    toast.remove(loadingToast);
                }
                toast.error(`خطأ في الاتصال: ${error.message}`);
            } finally {
                // Reset button state only if loading was shown
                if (!form.dataset.noLoading) {
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('btn-loading');
                    submitBtn.innerHTML = originalBtnText;
                }
            }
        });
    });
    
    // Handle delete buttons with confirmation
    document.addEventListener('click', function(e) {
        // Check if clicked element or its parent has data-confirm-delete
        const deleteBtn = e.target.closest('[data-confirm-delete]');
        
        if (deleteBtn) {
            e.preventDefault();
            
            const message = deleteBtn.dataset.confirmMessage || 'هل أنت متأكد من الحذف؟ هذا الإجراء لا يمكن التراجع عنه.';
            const deleteUrl = deleteBtn.dataset.deleteUrl || deleteBtn.href;
            
            // Custom confirmation dialog
            if (confirm(message)) {
                const loadingToast = toast.loading('جاري الحذف...');
                
                // Determine HTTP method
                const method = deleteBtn.dataset.method || 'POST';
                
                fetch(deleteUrl, {
                    method: method,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    }
                })
                .then(async response => {
                    toast.remove(loadingToast);
                    
                    const contentType = response.headers.get("content-type");
                    
                    if (response.ok) {
                        if (contentType && contentType.indexOf("application/json") !== -1) {
                            const data = await response.json();
                            toast.success(data.message || 'تم الحذف بنجاح');
                            
                            if (data.redirect) {
                                setTimeout(() => {
                                    window.location.href = data.redirect;
                                }, 1000);
                            }
                        } else {
                            toast.success('تم الحذف بنجاح');
                        }
                        
                        // Remove element from DOM if specified
                        const removeElement = deleteBtn.dataset.removeElement;
                        if (removeElement) {
                            const element = deleteBtn.closest(removeElement);
                            if (element) {
                                element.style.transition = 'all 0.3s ease-out';
                                element.style.transform = 'translateX(-100%)';
                                element.style.opacity = '0';
                                setTimeout(() => element.remove(), 300);
                            }
                        } else {
                            // Reload page after delay
                            setTimeout(() => location.reload(), 1000);
                        }
                    } else {
                        if (contentType && contentType.indexOf("application/json") !== -1) {
                            const data = await response.json();
                            toast.error(data.message || 'فشل الحذف');
                        } else {
                            const text = await response.text();
                            toast.error(text || 'فشل الحذف - الرجاء المحاولة مرة أخرى');
                        }
                    }
                })
                .catch(error => {
                    toast.remove(loadingToast);
                    toast.error(`خطأ في الاتصال: ${error.message}`);
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