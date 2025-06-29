// Form handling JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize form handlers
    initializeFormValidation();
    initializeFileUploads();
    initializeDynamicForms();
    initializeFormSubmissions();
});

function initializeFormValidation() {
    // Custom validation rules
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            form.classList.add('was-validated');
        });

        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(input);
            });
        });
    });
}

function validateField(field) {
    const fieldType = field.type || field.tagName.toLowerCase();
    const value = field.value.trim();
    
    // Custom validation based on field type
    switch (fieldType) {
        case 'email':
            return validateEmail(field, value);
        case 'tel':
            return validatePhone(field, value);
        case 'url':
            return validateUrl(field, value);
        default:
            return field.checkValidity();
    }
}

function validateEmail(field, value) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(value);
    
    if (!isValid && value !== '') {
        field.setCustomValidity('Please enter a valid email address');
    } else {
        field.setCustomValidity('');
    }
    
    return isValid;
}

function validatePhone(field, value) {
    const phoneRegex = /^254[17]\d{8}$/;
    const isValid = phoneRegex.test(value);
    
    if (!isValid && value !== '') {
        field.setCustomValidity('Please enter a valid Kenyan phone number (254XXXXXXXXX)');
    } else {
        field.setCustomValidity('');
    }
    
    return isValid;
}

function validateUrl(field, value) {
    try {
        new URL(value);
        field.setCustomValidity('');
        return true;
    } catch {
        if (value !== '') {
            field.setCustomValidity('Please enter a valid URL');
        } else {
            field.setCustomValidity('');
        }
        return false;
    }
}

function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            handleFileUpload(input);
        });
    });
}

function handleFileUpload(input) {
    const files = input.files;
    const maxSize = input.getAttribute('data-max-size') || 5 * 1024 * 1024; // 5MB default
    const allowedTypes = input.getAttribute('data-allowed-types');
    
    for (let file of files) {
        // Check file size
        if (file.size > maxSize) {
            showAlert(`File ${file.name} is too large. Maximum size is ${formatFileSize(maxSize)}.`, 'error');
            input.value = '';
            return;
        }
        
        // Check file type
        if (allowedTypes) {
            const types = allowedTypes.split(',').map(t => t.trim());
            if (!types.includes(file.type)) {
                showAlert(`File ${file.name} has an invalid type. Allowed types: ${allowedTypes}`, 'error');
                input.value = '';
                return;
            }
        }
    }
    
    // Show preview if applicable
    const preview = document.querySelector(input.getAttribute('data-preview'));
    if (preview && files.length > 0) {
        showFilePreview(files[0], preview);
    }
}

function showFilePreview(file, container) {
    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            container.innerHTML = `
                <div class="file-preview">
                    <img src="${e.target.result}" class="img-thumbnail" style="max-width: 200px; max-height: 200px;">
                    <p class="text-muted mt-2">${file.name} (${formatFileSize(file.size)})</p>
                </div>
            `;
        };
        reader.readAsDataURL(file);
    } else {
        container.innerHTML = `
            <div class="file-preview">
                <div class="file-icon">
                    <i class="fas fa-file fa-3x text-muted"></i>
                </div>
                <p class="text-muted mt-2">${file.name} (${formatFileSize(file.size)})</p>
            </div>
        `;
    }
}

function initializeDynamicForms() {
    // Handle dynamic form fields (like product variations)
    const addButtons = document.querySelectorAll('.add-field-btn');
    addButtons.forEach(button => {
        button.addEventListener('click', function() {
            const template = button.getAttribute('data-template');
            const container = document.querySelector(button.getAttribute('data-container'));
            
            if (template && container) {
                addDynamicField(template, container);
            }
        });
    });
    
    // Handle remove buttons
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('remove-field-btn')) {
            const fieldGroup = event.target.closest('.dynamic-field-group');
            if (fieldGroup) {
                fieldGroup.remove();
            }
        }
    });
}

function addDynamicField(templateId, container) {
    const template = document.getElementById(templateId);
    if (template) {
        const clone = template.content.cloneNode(true);
        
        // Update field names and IDs to be unique
        const index = container.children.length;
        const inputs = clone.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.name) {
                input.name = input.name.replace('__INDEX__', index);
            }
            if (input.id) {
                input.id = input.id.replace('__INDEX__', index);
            }
        });
        
        const labels = clone.querySelectorAll('label');
        labels.forEach(label => {
            if (label.getAttribute('for')) {
                label.setAttribute('for', label.getAttribute('for').replace('__INDEX__', index));
            }
        });
        
        container.appendChild(clone);
    }
}

function initializeFormSubmissions() {
    // Handle AJAX form submissions
    const ajaxForms = document.querySelectorAll('.ajax-form');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            submitAjaxForm(form);
        });
    });
}

function submitAjaxForm(form) {
    const submitButton = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    
    showLoading(submitButton);
    
    fetch(form.action, {
        method: form.method || 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading(submitButton);
        
        if (data.success) {
            showAlert(data.message || 'Operation completed successfully', 'success');
            
            // Handle redirect
            if (data.redirect) {
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            }
            
            // Reset form if needed
            if (data.reset_form) {
                form.reset();
                form.classList.remove('was-validated');
            }
        } else {
            showAlert(data.message || 'An error occurred', 'error');
            
            // Show field errors
            if (data.errors) {
                showFieldErrors(form, data.errors);
            }
        }
    })
    .catch(error => {
        hideLoading(submitButton);
        showAlert('An unexpected error occurred. Please try again.', 'error');
        console.error('Form submission error:', error);
    });
}

function showFieldErrors(form, errors) {
    // Clear previous errors
    const errorElements = form.querySelectorAll('.field-error');
    errorElements.forEach(el => el.remove());
    
    // Show new errors
    Object.keys(errors).forEach(fieldName => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'field-error text-danger small mt-1';
            errorDiv.textContent = errors[fieldName];
            field.parentNode.appendChild(errorDiv);
        }
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Export for global use
window.Forms = {
    validateField,
    validateEmail,
    validatePhone,
    validateUrl,
    submitAjaxForm,
    addDynamicField,
    formatFileSize
};
