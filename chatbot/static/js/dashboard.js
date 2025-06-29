// Dashboard specific JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }

    // Real-time updates for dashboard stats
    const statsContainer = document.querySelector('.dashboard-stats');
    if (statsContainer) {
        setInterval(updateDashboardStats, 30000); // Update every 30 seconds
    }

    // Initialize data tables if available
    if (typeof DataTable !== 'undefined') {
        initializeDataTables();
    }
});

function initializeCharts() {
    // Sales Chart
    const salesCtx = document.getElementById('salesChart');
    if (salesCtx) {
        new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Sales',
                    data: [],
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

    // Orders Chart
    const ordersCtx = document.getElementById('ordersChart');
    if (ordersCtx) {
        new Chart(ordersCtx, {
            type: 'doughnut',
            data: {
                labels: ['Pending', 'Processing', 'Completed', 'Cancelled'],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#ffc107',
                        '#0167bb',
                        '#58a15c',
                        '#dc3545'
                    ]
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

    // Products Chart
    const productsCtx = document.getElementById('productsChart');
    if (productsCtx) {
        new Chart(productsCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Stock Levels',
                    data: [],
                    backgroundColor: '#58a15c',
                    borderColor: '#58a15c',
                    borderWidth: 1
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

    // Load chart data
    loadChartData();
}

function loadChartData() {
    // Load sales data
    fetch('/api/analytics/sales-data')
        .then(response => response.json())
        .then(data => {
            const salesChart = Chart.getChart('salesChart');
            if (salesChart && data.success) {
                salesChart.data.labels = data.labels;
                salesChart.data.datasets[0].data = data.values;
                salesChart.update();
            }
        })
        .catch(error => console.error('Error loading sales data:', error));

    // Load orders data
    fetch('/api/analytics/orders-data')
        .then(response => response.json())
        .then(data => {
            const ordersChart = Chart.getChart('ordersChart');
            if (ordersChart && data.success) {
                ordersChart.data.datasets[0].data = data.values;
                ordersChart.update();
            }
        })
        .catch(error => console.error('Error loading orders data:', error));

    // Load products data
    fetch('/api/analytics/products-data')
        .then(response => response.json())
        .then(data => {
            const productsChart = Chart.getChart('productsChart');
            if (productsChart && data.success) {
                productsChart.data.labels = data.labels;
                productsChart.data.datasets[0].data = data.values;
                productsChart.update();
            }
        })
        .catch(error => console.error('Error loading products data:', error));
}

function updateDashboardStats() {
    fetch('/api/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStatCard('total-sales', data.total_sales);
                updateStatCard('total-orders', data.total_orders);
                updateStatCard('total-customers', data.total_customers);
                updateStatCard('total-products', data.total_products);
            }
        })
        .catch(error => console.error('Error updating dashboard stats:', error));
}

function updateStatCard(id, value) {
    const element = document.getElementById(id);
    if (element) {
        // Add animation effect
        element.style.transform = 'scale(1.05)';
        setTimeout(() => {
            element.textContent = typeof value === 'number' ? value.toLocaleString() : value;
            element.style.transform = 'scale(1)';
        }, 200);
    }
}

function initializeDataTables() {
    // Initialize all tables with class 'data-table'
    const tables = document.querySelectorAll('.data-table');
    tables.forEach(table => {
        new DataTable(table, {
            responsive: true,
            pageLength: 25,
            order: [[0, 'desc']],
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
            }
        });
    });
}

// Export for global use
window.Dashboard = {
    loadChartData,
    updateDashboardStats,
    updateStatCard
};
