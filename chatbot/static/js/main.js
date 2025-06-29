// Main JavaScript for SasaBot Application
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && alert.parentNode) {
                alert.style.opacity = '0';
                setTimeout(function() {
                    if (alert && alert.parentNode) {
                        alert.remove();
                    }
                }, 300);
            }
        }, 5000);
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const target = document.querySelector(button.getAttribute('data-target'));
            if (target) {
                navigator.clipboard.writeText(target.textContent || target.value).then(function() {
                    const originalText = button.textContent;
                    button.textContent = 'Copied!';
                    button.classList.add('btn-success');
                    setTimeout(function() {
                        button.textContent = originalText;
                        button.classList.remove('btn-success');
                    }, 2000);
                });
            }
        });
    });

    // Confirm delete dialogs
    const deleteButtons = document.querySelectorAll('.delete-btn, .btn-delete');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            const itemName = button.getAttribute('data-item') || 'this item';
            if (!confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`)) {
                event.preventDefault();
            }
        });
    });

    // Auto-refresh functionality for real-time data
    const autoRefreshElements = document.querySelectorAll('[data-auto-refresh]');
    autoRefreshElements.forEach(function(element) {
        const interval = parseInt(element.getAttribute('data-auto-refresh')) * 1000;
        if (interval > 0) {
            setInterval(function() {
                location.reload();
            }, interval);
        }
    });

    // Mobile menu toggle
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', function() {
            navbarCollapse.classList.toggle('show');
        });
    }

    // Search functionality
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(function(input) {
        const tableId = input.getAttribute('data-table');
        const table = document.getElementById(tableId);
        
        if (table) {
            input.addEventListener('keyup', function() {
                const filter = input.value.toLowerCase();
                const rows = table.getElementsByTagName('tr');
                
                for (let i = 1; i < rows.length; i++) {
                    const row = rows[i];
                    const cells = row.getElementsByTagName('td');
                    let found = false;
                    
                    for (let j = 0; j < cells.length; j++) {
                        if (cells[j].textContent.toLowerCase().indexOf(filter) > -1) {
                            found = true;
                            break;
                        }
                    }
                    
                    row.style.display = found ? '' : 'none';
                }
            });
        }
    });

    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const file = input.files[0];
            const preview = document.querySelector(input.getAttribute('data-preview'));
            
            if (file && preview) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    if (file.type.startsWith('image/')) {
                        preview.innerHTML = `<img src="${e.target.result}" class="img-thumbnail" style="max-width: 200px;">`;
                    } else {
                        preview.innerHTML = `<p class="text-muted">File selected: ${file.name}</p>`;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Price formatting
    const priceInputs = document.querySelectorAll('.price-input');
    priceInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            const value = parseFloat(input.value);
            if (!isNaN(value)) {
                input.value = value.toFixed(2);
            }
        });
    });

    // Phone number formatting
    const phoneInputs = document.querySelectorAll('.phone-input');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            let value = input.value.replace(/\D/g, '');
            if (value.length > 0 && !value.startsWith('254')) {
                if (value.startsWith('0')) {
                    value = '254' + value.substring(1);
                } else if (value.startsWith('7') || value.startsWith('1')) {
                    value = '254' + value;
                }
            }
            input.value = value;
        });
    });
});

// Utility functions
function showLoading(button) {
    if (button) {
        button.disabled = true;
        const originalText = button.textContent;
        button.setAttribute('data-original-text', originalText);
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    }
}

function hideLoading(button) {
    if (button) {
        button.disabled = false;
        const originalText = button.getAttribute('data-original-text');
        if (originalText) {
            button.textContent = originalText;
        }
    }
}

function showAlert(message, type = 'info', container = '.alert-container') {
    const alertContainer = document.querySelector(container);
    if (alertContainer) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alertContainer.appendChild(alertDiv);
        
        // Auto-hide after 5 seconds
        setTimeout(function() {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.style.opacity = '0';
                setTimeout(function() {
                    if (alertDiv && alertDiv.parentNode) {
                        alertDiv.remove();
                    }
                }, 300);
            }
        }, 5000);
    }
}

function formatCurrency(amount, currency = 'KES') {
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-KE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function validateWhatsAppNumber(number) {
    // Remove all non-digit characters
    const cleanNumber = number.replace(/\D/g, '');
    
    // Check if it's a valid Kenyan number
    if (cleanNumber.length === 12 && cleanNumber.startsWith('254')) {
        return cleanNumber;
    } else if (cleanNumber.length === 10 && cleanNumber.startsWith('0')) {
        return '254' + cleanNumber.substring(1);
    } else if (cleanNumber.length === 9 && (cleanNumber.startsWith('7') || cleanNumber.startsWith('1'))) {
        return '254' + cleanNumber;
    }
    
    return null;
}

// Export functions for use in other scripts
window.SasaBot = {
    showLoading,
    hideLoading,
    showAlert,
    formatCurrency,
    formatDate,
    validateWhatsAppNumber
};
