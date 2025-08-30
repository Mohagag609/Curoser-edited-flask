/**
 * Dashboard Live Updates
 * تحديثات لوحة التحكم الحية
 */

class DashboardLive {
    constructor() {
        this.updateInterval = 30000; // 30 ثانية
        this.charts = {};
        this.isUpdating = false;
    }

    init() {
        this.setupCharts();
        this.startAutoUpdate();
        this.bindEvents();
    }

    setupCharts() {
        // مخطط المبيعات
        const salesCtx = document.getElementById('salesChart');
        if (salesCtx) {
            this.charts.sales = new Chart(salesCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'المبيعات',
                        data: [],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
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
                                    return value.toLocaleString('ar-EG') + ' ج.م';
                                }
                            }
                        }
                    }
                }
            });
        }

        // مخطط الوحدات
        const unitsCtx = document.getElementById('unitsChart');
        if (unitsCtx) {
            this.charts.units = new Chart(unitsCtx, {
                type: 'doughnut',
                data: {
                    labels: ['متاحة', 'محجوزة', 'مباعة'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: [
                            'rgb(34, 197, 94)',
                            'rgb(251, 191, 36)',
                            'rgb(239, 68, 68)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                font: {
                                    family: 'Tajawal'
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    async updateDashboard() {
        if (this.isUpdating) return;
        
        this.isUpdating = true;
        this.showLoadingIndicator();

        try {
            const response = await fetch('/dashboard/api/stats', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            this.updateStats(data);
            this.updateCharts(data);
            this.showSuccessIndicator();

        } catch (error) {
            console.error('Error updating dashboard:', error);
            this.showErrorIndicator();
        } finally {
            this.isUpdating = false;
        }
    }

    updateStats(data) {
        // تحديث الإحصائيات
        const updateElement = (id, value) => {
            const element = document.getElementById(id);
            if (element) {
                const currentValue = parseInt(element.textContent.replace(/[^0-9]/g, '')) || 0;
                this.animateValue(element, currentValue, value);
            }
        };

        updateElement('totalContracts', data.contracts?.total || 0);
        updateElement('totalUnits', data.units?.total || 0);
        updateElement('totalRevenue', data.finance?.income || 0);
        updateElement('totalCustomers', data.customers || 0);
    }

    animateValue(element, start, end, duration = 1000) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                current = end;
                clearInterval(timer);
            }
            element.textContent = Math.round(current).toLocaleString('ar-EG');
        }, 16);
    }

    updateCharts(data) {
        // تحديث مخطط المبيعات
        if (this.charts.sales && data.sales_trend) {
            this.charts.sales.data.labels = data.sales_trend.labels;
            this.charts.sales.data.datasets[0].data = data.sales_trend.values;
            this.charts.sales.update('none'); // بدون animation
        }

        // تحديث مخطط الوحدات
        if (this.charts.units && data.units) {
            const unitsData = [
                data.units.by_status?.['متاحة'] || 0,
                data.units.by_status?.['محجوزة'] || 0,
                data.units.by_status?.['مباعة'] || 0
            ];
            this.charts.units.data.datasets[0].data = unitsData;
            this.charts.units.update('none');
        }
    }

    startAutoUpdate() {
        // تحديث أول مرة
        this.updateDashboard();

        // تحديث دوري
        this.updateTimer = setInterval(() => {
            this.updateDashboard();
        }, this.updateInterval);
    }

    stopAutoUpdate() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
    }

    bindEvents() {
        // إيقاف التحديث عند مغادرة الصفحة
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoUpdate();
            } else {
                this.startAutoUpdate();
            }
        });

        // زر التحديث اليدوي
        const refreshBtn = document.getElementById('refreshDashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.updateDashboard();
            });
        }
    }

    showLoadingIndicator() {
        const indicator = document.getElementById('updateIndicator');
        if (indicator) {
            indicator.className = 'text-blue-500';
            indicator.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i>';
        }
    }

    showSuccessIndicator() {
        const indicator = document.getElementById('updateIndicator');
        if (indicator) {
            indicator.className = 'text-green-500';
            indicator.innerHTML = '<i class="fas fa-check-circle"></i>';
            setTimeout(() => {
                indicator.innerHTML = '';
            }, 2000);
        }
    }

    showErrorIndicator() {
        const indicator = document.getElementById('updateIndicator');
        if (indicator) {
            indicator.className = 'text-red-500';
            indicator.innerHTML = '<i class="fas fa-exclamation-circle"></i>';
        }
    }
}

// تهيئة عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('dashboardContainer')) {
        window.dashboardLive = new DashboardLive();
        window.dashboardLive.init();
    }
});