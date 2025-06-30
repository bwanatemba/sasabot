// SasaBot Custom JavaScript

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    // Wait for jQuery to be available
    if (typeof jQuery !== 'undefined') {
        initializeApp();
    } else {
        // Retry after a short delay if jQuery is not yet loaded
        setTimeout(function() {
            if (typeof jQuery !== 'undefined') {
                initializeApp();
            } else {
                console.error('jQuery is not available. Some features may not work properly.');
                initializeAppWithoutJQuery();
            }
        }, 100);
    }
});

function initializeApp() {
    initializeTooltips();
    initializePopovers();
    initializeFileUploads();
    initializeCharts();
    initializeFormValidation();
    initializeDataTables();
    initializeBulkActions();
    initializeRealTimeUpdates();
}

function initializeAppWithoutJQuery() {
    initializeTooltips();
    initializePopovers();
    initializeFileUploads();
    initializeCharts();
    initializeFormValidation();
    initializeBulkActions();
    initializeRealTimeUpdates();
}

// Initialize Bootstrap Tooltips
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize Bootstrap Popovers
function initializePopovers() {
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// File Upload Functionality
function initializeFileUploads() {
    const fileUploadAreas = document.querySelectorAll('.file-upload-area');
    
    fileUploadAreas.forEach(area => {
        const input = area.querySelector('input[type="file"]');
        
        if (input) {
            // Drag and drop events
            area.addEventListener('dragover', function(e) {
                e.preventDefault();
                area.classList.add('dragover');
            });
            
            area.addEventListener('dragleave', function(e) {
                e.preventDefault();
                area.classList.remove('dragover');
            });
            
            area.addEventListener('drop', function(e) {
                e.preventDefault();
                area.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    input.files = files;
                    displaySelectedFiles(input, area);
                }
            });
            
            // Click to select
            area.addEventListener('click', function() {
                input.click();
            });
            
            // File input change
            input.addEventListener('change', function() {
                displaySelectedFiles(input, area);
            });
        }
    });
}

function displaySelectedFiles(input, area) {
    const files = input.files;
    const fileList = area.querySelector('.file-list') || createFileList(area);
    
    fileList.innerHTML = '';
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item d-flex justify-content-between align-items-center mb-2';
        fileItem.innerHTML = `
            <span><i class="fas fa-file"></i> ${file.name} (${formatFileSize(file.size)})</span>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFile(${i})">
                <i class="fas fa-times"></i>
            </button>
        `;
        fileList.appendChild(fileItem);
    }
}

function createFileList(area) {
    const fileList = document.createElement('div');
    fileList.className = 'file-list mt-3';
    area.appendChild(fileList);
    return fileList;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Chart Initialization
function initializeCharts() {
    initializeDashboardCharts();
    initializeAnalyticsCharts();
}

function initializeDashboardCharts() {
    // Sales Chart
    const salesChartCtx = document.getElementById('salesChart');
    if (salesChartCtx) {
        new Chart(salesChartCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Sales',
                    data: [12, 19, 3, 5, 2, 3],
                    borderColor: '#0167bb',
                    backgroundColor: 'rgba(1, 103, 187, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Orders Chart
    const ordersChartCtx = document.getElementById('ordersChart');
    if (ordersChartCtx) {
        new Chart(ordersChartCtx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'Pending', 'Cancelled'],
                datasets: [{
                    data: [65, 25, 10],
                    backgroundColor: ['#58a15c', '#ffc107', '#dc3545']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
}

function initializeAnalyticsCharts() {
    // Revenue Chart
    const revenueChartCtx = document.getElementById('revenueChart');
    if (revenueChartCtx) {
        new Chart(revenueChartCtx, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Revenue',
                    data: [1200, 1900, 800, 1500, 2000, 2400, 1800],
                    backgroundColor: '#0167bb'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'KES ' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
}

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// DataTables Initialization
function initializeDataTables() {
    if (typeof $ !== 'undefined' && typeof $.fn.DataTable !== 'undefined') {
        $('.data-table').DataTable({
            responsive: true,
            pageLength: 25,
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            },
            dom: '<"row"<"col-sm-6"l><"col-sm-6"f>>' +
                 '<"row"<"col-sm-12"tr>>' +
                 '<"row"<"col-sm-5"i><"col-sm-7"p>>',
            columnDefs: [
                { orderable: false, targets: 'no-sort' }
            ]
        });
    } else {
        console.warn('jQuery or DataTables not available. Tables will display without enhanced functionality.');
    }
}

// Bulk Actions
function initializeBulkActions() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');
    const bulkActionBtn = document.getElementById('bulkActionBtn');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            itemCheckboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
            updateBulkActionButton();
        });
    }
    
    itemCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectAllCheckbox();
            updateBulkActionButton();
        });
    });
    
    function updateSelectAllCheckbox() {
        const checkedCount = document.querySelectorAll('.item-checkbox:checked').length;
        const totalCount = itemCheckboxes.length;
        
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = checkedCount === totalCount;
            selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < totalCount;
        }
    }
    
    function updateBulkActionButton() {
        const checkedCount = document.querySelectorAll('.item-checkbox:checked').length;
        if (bulkActionBtn) {
            bulkActionBtn.style.display = checkedCount > 0 ? 'block' : 'none';
            bulkActionBtn.textContent = `Actions (${checkedCount} selected)`;
        }
    }
}

// Real-time Updates
function initializeRealTimeUpdates() {
    // Update timestamps
    updateTimestamps();
    setInterval(updateTimestamps, 60000); // Update every minute
    
    // Check for new notifications
    if (document.querySelector('.notification-bell')) {
        checkNotifications();
        setInterval(checkNotifications, 30000); // Check every 30 seconds
    }
}

function updateTimestamps() {
    const timestamps = document.querySelectorAll('[data-timestamp]');
    timestamps.forEach(element => {
        const timestamp = parseInt(element.dataset.timestamp);
        const now = Date.now();
        const diff = now - timestamp;
        
        element.textContent = formatTimeAgo(diff);
    });
}

function formatTimeAgo(diff) {
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
}

function checkNotifications() {
    fetch('/api/notifications/count')
        .then(response => response.json())
        .then(data => {
            const badge = document.querySelector('.notification-badge');
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count;
                    badge.style.display = 'inline';
                } else {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error checking notifications:', error));
}

// Utility Functions
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.id = 'alertContainer';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

function formatCurrency(amount, currency = 'KES') {
    return new Intl.NumberFormat('en-KE', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function formatNumber(number) {
    return new Intl.NumberFormat('en-KE').format(number);
}

// Export/Import Functions
function exportData(format, data, filename) {
    if (format === 'csv') {
        exportToCSV(data, filename);
    } else if (format === 'xlsx') {
        exportToExcel(data, filename);
    }
}

function exportToCSV(data, filename) {
    const csv = Papa.unparse(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    downloadBlob(blob, filename + '.csv');
}

function exportToExcel(data, filename) {
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
    XLSX.writeFile(wb, filename + '.xlsx');
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Chat Interface Functions
function initializeChatInterface() {
    const chatContainer = document.querySelector('.chat-messages');
    const chatInput = document.querySelector('.chat-input input');
    const sendButton = document.querySelector('.chat-input button');
    
    if (chatInput && sendButton) {
        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Auto-scroll to bottom
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

function sendMessage() {
    const chatInput = document.querySelector('.chat-input input');
    const message = chatInput.value.trim();
    
    if (message) {
        addMessageToChat(message, 'sent');
        chatInput.value = '';
        
        // Simulate response (replace with actual API call)
        setTimeout(() => {
            addMessageToChat('Thank you for your message. How can I help you?', 'received');
        }, 1000);
    }
}

function addMessageToChat(message, type) {
    const chatContainer = document.querySelector('.chat-messages');
    if (chatContainer) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Product Management Functions
function toggleProductStatus(productId) {
    fetch(`/vendor/products/${productId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            showAlert('Error updating product status', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error updating product status', 'error');
    });
}

function deleteProduct(productId) {
    confirmAction('Are you sure you want to delete this product?', () => {
        fetch(`/vendor/products/${productId}/delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                showAlert('Error deleting product', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error deleting product', 'error');
        });
    });
}

// Order Management Functions
function updateOrderStatus(orderId, status) {
    fetch(`/vendor/orders/${orderId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Order status updated successfully', 'success');
            location.reload();
        } else {
            showAlert('Error updating order status', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error updating order status', 'error');
    });
}

// Utility function to get CSRF token
function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

// WhatsApp Integration Functions
function testWhatsAppConnection(businessId) {
    fetch(`/vendor/businesses/${businessId}/test-whatsapp`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('WhatsApp connection test successful!', 'success');
        } else {
            showAlert('WhatsApp connection test failed: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error testing WhatsApp connection', 'error');
    });
}

// Analytics Functions
function refreshAnalytics() {
    const analyticsContainer = document.querySelector('.analytics-container');
    if (analyticsContainer) {
        analyticsContainer.style.opacity = '0.5';
        
        fetch('/vendor/analytics/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                showAlert('Error refreshing analytics', 'error');
                analyticsContainer.style.opacity = '1';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error refreshing analytics', 'error');
            analyticsContainer.style.opacity = '1';
        });
    }
}

// Print Functions
function printPage() {
    window.print();
}

function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Print</title>
                    <link rel="stylesheet" href="/static/css/custom.css">
                    <style>
                        body { font-family: Arial, sans-serif; }
                        @media print {
                            body { margin: 0; }
                            .no-print { display: none !important; }
                        }
                    </style>
                </head>
                <body>
                    ${element.innerHTML}
                    <script>window.print(); window.close();</script>
                </body>
            </html>
        `);
    }
}

// Search Functions
function initializeSearch() {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(performSearch, 300));
    }
}

function performSearch() {
    const searchInput = document.querySelector('.search-input');
    const query = searchInput.value.trim();
    
    if (query.length >= 2) {
        // Implement search logic here
        console.log('Searching for:', query);
    }
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize search on load
document.addEventListener('DOMContentLoaded', initializeSearch);
