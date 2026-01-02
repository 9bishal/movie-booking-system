/**
 * dashboard.js - Admin Dashboard Logic
 * ------------------------------------
 * Handles fetching data from Django API endpoints and rendering charts.
 * Uses a class-based structure for better state management.
 */

class Dashboard {
    constructor() {
        this.charts = {};
        this.init();
    }
    
    init() {
        // Load initial data (default 30 days)
        this.loadRevenueData(30);
        this.loadUserData();
        this.loadMovieData();
        this.loadTheaterData();
        this.loadRealtimeStats();
        
        // Set up auto-refresh
        setInterval(() => this.loadRealtimeStats(), 30000); // Every 30 seconds
        
        // Set up event listeners
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Date range selector
        document.querySelectorAll('[data-range]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const range = btn.dataset.range;
                this.updateDateRange(range);
            });
        });
        
        // Chart type selector
        document.querySelectorAll('[data-chart]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const type = btn.dataset.chart;
                this.updateRevenueChart(type);
            });
        });
        
        // Refresh system status
        const refreshBtn = document.getElementById('refreshStatus');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadSystemStatus();
            });
            // Also load on init
            this.loadSystemStatus();
        }
    }
    
    async loadRevenueData(days = 30) {
        try {
            const response = await fetch(`/admin/dashboard/api/revenue-data/?days=${days}`);
            const data = await response.json();
            
            this.updateStats(data);
            this.renderRevenueChart(data);
            this.renderMoviePieChart(data); // Using revenue data which includes top movies
        } catch (error) {
            console.error('Error loading revenue data:', error);
        }
    }
    
    async loadUserData() {
        try {
            const response = await fetch('/admin/dashboard/api/user-activity/');
            const data = await response.json();
            this.renderUserChart(data);
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    }
    
    async loadMovieData() {
        try {
            const response = await fetch('/admin/dashboard/api/movie-performance/');
            const data = await response.json();
            this.renderMovieChart(data);
        } catch (error) {
            console.error('Error loading movie data:', error);
        }
    }
    
    async loadTheaterData() {
        try {
            const response = await fetch('/admin/dashboard/api/theater-performance/');
            const data = await response.json();
            this.renderTheaterChart(data);
        } catch (error) {
            console.error('Error loading theater data:', error);
        }
    }
    
    async loadRealtimeStats() {
        try {
            const response = await fetch('/admin/dashboard/api/realtime-stats/');
            const data = await response.json();
            this.updateRealtimeStats(data);
        } catch (error) {
            console.error('Error loading realtime stats:', error);
        }
    }
    
    async loadSystemStatus() {
        try {
            const container = document.getElementById('systemStatus');
            if (container) {
                container.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div> Checking...</div>';
            }
            
            const response = await fetch('/admin/dashboard/api/system-status/');
            const data = await response.json();
            this.renderSystemStatus(data);
        } catch (error) {
            console.error('Error loading system status:', error);
        }
    }
    
    updateStats(data) {
        // Calculate totals
        const totalRevenue = data.daily_revenue.reduce((a, b) => a + b, 0);
        const totalBookings = data.daily_bookings.reduce((a, b) => a + b, 0);
        const avgTicketPrice = totalBookings > 0 ? totalRevenue / totalBookings : 0;
        
        // Update DOM elements if they exist
        const revenueEl = document.getElementById('totalRevenue');
        if (revenueEl) revenueEl.textContent = `₹${totalRevenue.toLocaleString()}`;
        
        const bookingEl = document.getElementById('totalBookings');
        if (bookingEl) bookingEl.textContent = totalBookings.toLocaleString();
        
        const priceEl = document.getElementById('avgTicketPrice');
        if (priceEl) priceEl.textContent = `₹${avgTicketPrice.toFixed(2)}`;
        
        // Calculate growth (simplified logic)
        // Note: Real production logic would compare strictly determined date ranges
        const lastWeekRevenue = data.daily_revenue.slice(-7).reduce((a, b) => a + b, 0);
        const prevWeekRevenue = data.daily_revenue.slice(-14, -7).reduce((a, b) => a + b, 0);
        const revenueGrowth = prevWeekRevenue > 0 ? ((lastWeekRevenue - prevWeekRevenue) / prevWeekRevenue * 100).toFixed(1) : 0;
        
        const revenueGrowthEl = document.getElementById('revenueGrowth');
        if (revenueGrowthEl) {
            revenueGrowthEl.innerHTML = `<i class="fas fa-arrow-${revenueGrowth >= 0 ? 'up' : 'down'}"></i> ${Math.abs(revenueGrowth)}%`;
            revenueGrowthEl.className = revenueGrowth >= 0 ? 'text-success mr-2' : 'text-danger mr-2';
        }
    }
    
    renderRevenueChart(data) {
        const canvas = document.getElementById('revenueChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts.revenue) {
            this.charts.revenue.destroy();
        }
        
        this.charts.revenue = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates.map(date => {
                    const d = new Date(date);
                    return `${d.getDate()}/${d.getMonth() + 1}`;
                }),
                datasets: [{
                    label: 'Revenue (₹)',
                    data: data.daily_revenue,
                    borderColor: '#4e73df',
                    backgroundColor: 'rgba(78, 115, 223, 0.05)',
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Bookings',
                    data: data.daily_bookings,
                    borderColor: '#1cc88a',
                    backgroundColor: 'rgba(28, 200, 138, 0.05)',
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) { return '₹' + value.toLocaleString(); }
                        }
                    },
                    y1: {
                        position: 'right',
                        beginAtZero: true,
                        grid: { drawOnChartArea: false }
                    }
                },
                plugins: {
                    legend: { display: true, position: 'top' }
                }
            }
        });
    }
    
    renderMoviePieChart(data) {
        const canvas = document.getElementById('moviePieChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts.moviePie) {
            this.charts.moviePie.destroy();
        }
        
        const colors = [
            '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', 
            '#e74a3b', '#858796', '#6f42c1', '#fd7e14'
        ];
        
        // Note: API returns 'top_movies' (list of dicts)
        this.charts.moviePie = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.top_movies.map(m => m.title),
                datasets: [{
                    data: data.top_movies.map(m => m.revenue),
                    backgroundColor: colors,
                    hoverBackgroundColor: colors,
                    hoverBorderColor: "rgba(234, 236, 244, 1)"
                }]
            },
            options: {
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: { display: false }
                }
            }
        });
        
        // Update legend
        const legendEl = document.getElementById('movieLegend');
        if (legendEl) {
            legendEl.innerHTML = data.top_movies.map((movie, i) => `
                <span class="me-4">
                    <i class="fas fa-circle" style="color: ${colors[i % colors.length]}"></i>
                    ${movie.title}
                </span>
            `).join('');
        }
    }
    
    renderUserChart(data) {
        const canvas = document.getElementById('userGrowthChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts.user) {
            this.charts.user.destroy();
        }
        
        this.charts.user = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.dates,
                datasets: [{
                    label: 'New Users',
                    data: data.new_users,
                    backgroundColor: 'rgba(78, 115, 223, 0.8)'
                }, {
                    label: 'Active Users',
                    data: data.active_users,
                    backgroundColor: 'rgba(28, 200, 138, 0.8)'
                }]
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, ticks: { stepSize: 1 } }
                },
                plugins: {
                    legend: { display: true, position: 'top' }
                }
            }
        });
        
        // Also update Active Users count card if present
        const activeUserEl = document.getElementById('activeUsers');
        if (activeUserEl && data.total_users) {
            activeUserEl.textContent = data.total_users;
        }
    }
    
    renderMovieChart(data) {
        // This would be used if we had a movie bar chart
        // Currently using pie chart for movies via loadRevenueData / renderMoviePieChart
    }
    
    renderTheaterChart(data) {
        const canvas = document.getElementById('theaterChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        if (this.charts.theater) {
            this.charts.theater.destroy();
        }
        
        const theaters = data.theaters.slice(0, 5); // Top 5 theaters
        const labels = theaters.map(t => t.name.split(' ')[0]); // First word of theater name
        const revenue = theaters.map(t => t.revenue);
        const occupancy = theaters.map(t => t.occupancy);
        
        this.charts.theater = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Revenue (₹)',
                    data: revenue,
                    backgroundColor: 'rgba(54, 185, 204, 0.8)',
                    yAxisID: 'y'
                }, {
                    label: 'Occupancy (%)',
                    data: occupancy,
                    backgroundColor: 'rgba(246, 194, 62, 0.8)',
                    yAxisID: 'y1',
                    type: 'line'
                }]
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false } },
                    y: {
                        beginAtZero: true,
                        ticks: { callback: function(value) { return '₹' + value.toLocaleString(); } }
                    },
                    y1: {
                        position: 'right',
                        beginAtZero: true,
                        max: 100,
                        grid: { drawOnChartArea: false },
                        ticks: { callback: function(value) { return value + '%'; } }
                    }
                },
                plugins: {
                    legend: { display: true, position: 'top' }
                }
            }
        });
    }
    
    updateRealtimeStats(data) {
        // Update today's stats if the elements exist
        // Note: Your analytics.html has ID `activeUsers` for total users, not "Confirmed + Pending"
        // But we can update the dashboard-header quick stats based on API return
        
        // Update recent bookings table
        const tbody = document.getElementById('recentBookingsBody');
        if (tbody) {
            tbody.innerHTML = data.recent_activity.map(activity => `
                <tr>
                    <td>${activity.user}</td>
                    <td>${activity.movie}</td>
                    <td>₹${activity.amount}</td>
                    <td><span class="badge-status badge-${activity.status.toLowerCase()}">${activity.status}</span></td>
                </tr>
            `).join('');
        }
    }
    
    renderSystemStatus(data) {
        const container = document.getElementById('systemStatus');
        if (!container) return;
        
        const statusHtml = `
            <div class="row">
                ${Object.entries(data.status).map(([service, isOk]) => `
                    <div class="col-6 mb-3">
                        <div class="d-flex align-items-center">
                            <div class="me-3">
                                <i class="fas fa-${isOk ? 'check-circle text-success' : 'times-circle text-danger'} fa-2x"></i>
                            </div>
                            <div>
                                <h6 class="mb-0">${service.charAt(0).toUpperCase() + service.slice(1)}</h6>
                                <small class="text-muted">${isOk ? 'Operational' : 'Down'}</small>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="mt-3">
                <h6>System Messages:</h6>
                <div class="list-group">
                    ${data.messages.map(msg => `
                        <div class="list-group-item list-group-item-${msg.type === 'success' ? 'success' : msg.type === 'warning' ? 'warning' : 'danger'} py-2">
                            <i class="fas fa-${msg.type === 'success' ? 'check' : msg.type === 'warning' ? 'exclamation-triangle' : 'times'} me-2"></i>
                            ${msg.message}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        container.innerHTML = statusHtml;
    }
    
    updateDateRange(range) {
        const days = parseInt(range);
        if (isNaN(days)) return;
        
        // Update UI dropdown text
        const dropdownBtn = document.querySelector('.dropdown-toggle');
        if (dropdownBtn) {
            dropdownBtn.innerHTML = `<i class="fas fa-calendar me-2"></i>Last ${days} Days`;
        }
        
        // Reload revenue data with new range
        this.loadRevenueData(days);
    }
    
    updateRevenueChart(type) {
        console.log('Update chart type to:', type);
        // Placeholder for switching between Daily/Weekly/Monthly views
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});
