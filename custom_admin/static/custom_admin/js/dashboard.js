/**
 * Custom Admin Dashboard Application
 * 
 * This class manages all dashboard functionality including:
 * - Fetching real-time statistics from API endpoints
 * - Rendering interactive charts using Chart.js
 * - Populating data tables with booking information
 * - Error handling and user feedback
 * 
 * Architecture:
 * - API calls are made to /custom-admin/api/* endpoints
 * - All data is fetched asynchronously to prevent page blocking
 * - Charts are re-rendered when data updates
 * - HTML elements are populated using DOM manipulation
 */
class AdminDashboard {
    /**
     * Initialize dashboard with API base URL and setup
     */
    constructor() {
        // Store Chart.js instances for cleanup/refresh
        this.charts = {};
        // Base URL for all API endpoints
        this.apiBaseUrl = '/custom-admin/api';
        // Flag to prevent multiple simultaneous requests
        this.isLoading = false;
        // Initialize dashboard on page load
        this.init();
    }

    /**
     * Show error message to user
     * @param {string} message - Error message to display
     */
    showError(message) {
        const errorContainer = document.createElement('div');
        errorContainer.className = 'error-message';
        errorContainer.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <span>${this.escapeHtml(message)}</span>
        `;
        
        const mainContainer = document.querySelector('.container-main');
        if (mainContainer) {
            mainContainer.insertBefore(errorContainer, mainContainer.firstChild);
            
            setTimeout(() => {
                errorContainer.style.opacity = '0';
                errorContainer.style.transition = 'opacity 0.3s ease';
                setTimeout(() => errorContainer.remove(), 300);
            }, 5000);
        }
    }

    /**
     * Initialize dashboard by loading all data
     * 
     * Called automatically on page load via DOMContentLoaded event.
     * Loads stats, revenue data, bookings, and theaters in parallel.
     */
    async init() {
        if (this.isLoading) return;
        this.isLoading = true;
        
        try {
            // Load all data concurrently
            await Promise.all([
                this.loadStats(),
                this.loadRevenue(),
                this.loadBookings()
            ]);
            
            // Setup filter event listeners
            this.setupFilterListeners();
        } catch (error) {
            console.error('Error initializing dashboard:', error);
            this.showError('Failed to load dashboard data. Please refresh the page.');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Setup event listeners for filter controls
     */
    setupFilterListeners() {
        const dateFromInput = document.getElementById('dateFrom');
        const dateToInput = document.getElementById('dateTo');
        const movieFilterSelect = document.getElementById('movieFilter');
        const theaterFilterSelect = document.getElementById('theaterFilter');
        const applyFiltersBtn = document.getElementById('applyFiltersBtn');
        const resetFiltersBtn = document.getElementById('resetFiltersBtn');
        const bookingsTable = document.getElementById('bookingsTable');

        if (!applyFiltersBtn || !resetFiltersBtn) {
            console.warn('Filter buttons not found');
            return;
        }

        // Populate movie and theater dropdown options
        this.populateFilterOptions();

        // Use arrow function to preserve 'this' context
        const applyFilters = async () => {
            const dateFrom = dateFromInput.value;
            const dateTo = dateToInput.value;
            const movie = movieFilterSelect.value;
            const theater = theaterFilterSelect.value;

            // Show loading state
            if (bookingsTable) {
                bookingsTable.innerHTML = '<tr><td colspan="3" class="text-center text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Filtering...</td></tr>';
            }

            try {
                // Build query parameters
                const params = new URLSearchParams();
                if (dateFrom) params.append('date_from', dateFrom);
                if (dateTo) params.append('date_to', dateTo);
                if (movie) params.append('movie', movie);
                if (theater) params.append('theater', theater);

                // Fetch filtered data from API
                const queryString = params.toString() ? '?' + params.toString() : '';
                const response = await fetch(`${this.apiBaseUrl}/dashboard-filtered/${queryString}`);
                
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }

                const data = await response.json();
                
                console.log('Filtered data received:', data);
                
                // Update stats with filtered data
                this.updateFilteredStats(data);
                
                // Destroy old charts before rendering new ones
                if (this.charts.revenue) this.charts.revenue.destroy();
                if (this.charts.movies) this.charts.movies.destroy();
                if (this.charts.theaters) this.charts.theaters.destroy();
                
                // Re-render all charts with filtered data
                if (data.revenue_data) {
                    this.renderRevenueChart(data.revenue_data);
                }
                if (data.top_movies && data.top_movies.length > 0) {
                    this.renderMoviesChart(data.top_movies);
                }
                if (data.top_theaters && data.top_theaters.length > 0) {
                    this.renderTheatersChart(data.top_theaters);
                }
                
                // Render filtered bookings
                if (bookingsTable) {
                    this.renderBookingsTable(data.recent_bookings || []);
                }
                
            } catch (error) {
                console.error('Error applying filters:', error);
                if (bookingsTable) {
                    bookingsTable.innerHTML = '<tr><td colspan="3" class="text-center text-danger"><i class="fas fa-exclamation-circle me-2"></i>Error loading filtered data</td></tr>';
                }
            }
        };

        const resetFilters = async () => {
            dateFromInput.value = '';
            dateToInput.value = '';
            movieFilterSelect.value = '';
            theaterFilterSelect.value = '';
            
            // Reload all data
            await this.init();
        };

        // Add event listeners
        applyFiltersBtn.addEventListener('click', applyFilters);
        resetFiltersBtn.addEventListener('click', resetFilters);
        
        // Also allow Enter key to apply filters
        dateFromInput.addEventListener('keypress', (e) => e.key === 'Enter' && applyFilters());
        dateToInput.addEventListener('keypress', (e) => e.key === 'Enter' && applyFilters());
    }

    /**
     * Populate filter dropdown options
     */
    async populateFilterOptions() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/filter-options/`);
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const data = await response.json();
            
            // Populate movies dropdown
            const movieFilterSelect = document.getElementById('movieFilter');
            if (movieFilterSelect && data.movies) {
                data.movies.forEach(movie => {
                    const option = document.createElement('option');
                    option.value = movie.id;
                    option.textContent = movie.title;
                    movieFilterSelect.appendChild(option);
                });
            }
            
            // Populate theaters dropdown
            const theaterFilterSelect = document.getElementById('theaterFilter');
            if (theaterFilterSelect && data.theaters) {
                data.theaters.forEach(theater => {
                    const option = document.createElement('option');
                    option.value = theater.id;
                    option.textContent = theater.name;
                    theaterFilterSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error populating filter options:', error);
        }
    }

    /**
     * Update stats based on filtered data
     */
    updateFilteredStats(data) {
        const totalRevenueEl = document.getElementById('totalRevenue');
        const totalBookingsEl = document.getElementById('totalBookings');
        const todayRevenueEl = document.getElementById('todayRevenue');
        const todayBookingsEl = document.getElementById('todayBookings');

        if (totalRevenueEl && data.total_revenue !== undefined) {
            totalRevenueEl.textContent = '₹' + (data.total_revenue || 0).toLocaleString('en-IN', {
                maximumFractionDigits: 2,
                minimumFractionDigits: 0
            });
        }

        if (totalBookingsEl && data.total_bookings !== undefined) {
            totalBookingsEl.textContent = (data.total_bookings || 0).toLocaleString('en-IN');
        }

        if (todayRevenueEl && data.today_revenue !== undefined) {
            todayRevenueEl.textContent = '₹' + (data.today_revenue || 0).toLocaleString('en-IN', {
                maximumFractionDigits: 2,
                minimumFractionDigits: 0
            });
        }

        if (todayBookingsEl && data.today_bookings !== undefined) {
            todayBookingsEl.textContent = (data.today_bookings || 0).toLocaleString('en-IN');
        }
    }

    /**
     * Load and display summary statistics
     * 
     * Fetches: Total revenue, today's revenue, total bookings, today's bookings
     * Updates stat cards with formatted currency and numbers
     * 
     * API: GET /custom-admin/api/stats/
     * Returns: {total_revenue, today_revenue, total_bookings, today_bookings}
     */
    async loadStats() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/stats/`);
            if (!response.ok) {
                throw new Error(`Stats API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Validate data
            if (typeof data.total_revenue !== 'number' || 
                typeof data.today_revenue !== 'number' ||
                typeof data.total_bookings !== 'number' ||
                typeof data.today_bookings !== 'number') {
                throw new Error('Invalid stats data format');
            }
            
            // Update total revenue card with formatted currency
            const totalRevenueEl = document.getElementById('totalRevenue');
            if (totalRevenueEl) {
                totalRevenueEl.textContent = '₹' + (data.total_revenue || 0).toLocaleString('en-IN', {
                    maximumFractionDigits: 2,
                    minimumFractionDigits: 0
                });
            }
            
            // Update total bookings count
            const totalBookingsEl = document.getElementById('totalBookings');
            if (totalBookingsEl) {
                totalBookingsEl.textContent = (data.total_bookings || 0).toLocaleString('en-IN');
            }
            
            // Update today's revenue with formatted currency
            const todayRevenueEl = document.getElementById('todayRevenue');
            if (todayRevenueEl) {
                todayRevenueEl.textContent = '₹' + (data.today_revenue || 0).toLocaleString('en-IN', {
                    maximumFractionDigits: 2,
                    minimumFractionDigits: 0
                });
            }
            
            // Update today's bookings count
            const todayBookingsEl = document.getElementById('todayBookings');
            if (todayBookingsEl) {
                todayBookingsEl.textContent = (data.today_bookings || 0).toLocaleString('en-IN');
            }
        } catch (error) {
            console.error('Error loading stats:', error);
            this.showError('Failed to load statistics. Please try again.');
        }
    }

    /**
     * Load and render 30-day revenue trend chart
     * 
     * Fetches daily revenue data for the last 30 days
     * Renders as a line chart with smooth curves
     * 
     * API: GET /custom-admin/api/revenue/?days=30
     * Returns: {dates: [...], revenues: [...]}
     */
    async loadRevenue() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/revenue/?days=30`);
            if (!response.ok) {
                throw new Error(`Revenue API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Validate data
            if (!Array.isArray(data.dates) || !Array.isArray(data.revenues)) {
                throw new Error('Invalid revenue data format');
            }
            
            if (data.dates.length === 0 || data.revenues.length === 0) {
                console.warn('No revenue data available');
            }
            
            this.renderRevenueChart(data);
        } catch (error) {
            console.error('Error loading revenue:', error);
            this.showError('Failed to load revenue chart.');
        }
    }

    /**
     * Load and render movies and bookings data
     * 
     * Fetches two datasets:
     * 1. Top 5 movies by booking count
     * 2. Recent 5 bookings with user, movie, amount info
     * 
     * API: GET /custom-admin/api/bookings/
     * Returns: {movies: [...], bookings: [...]}
     */
    async loadBookings() {
        try {
            const [bookingsResponse, theatersResponse] = await Promise.all([
                fetch(`${this.apiBaseUrl}/bookings/`),
                fetch(`${this.apiBaseUrl}/theaters/`)
            ]);
            
            if (!bookingsResponse.ok) {
                throw new Error(`Bookings API error: ${bookingsResponse.status}`);
            }
            
            const bookingsData = await bookingsResponse.json();
            
            // Validate bookings data
            if (!Array.isArray(bookingsData.movies) || !Array.isArray(bookingsData.bookings)) {
                throw new Error('Invalid bookings data format');
            }
            
            // Render top movies bar chart
            this.renderMoviesChart(bookingsData.movies);
            // Populate recent bookings table
            this.renderBookingsTable(bookingsData.bookings);
            
            // Handle theaters data if available
            if (theatersResponse.ok) {
                const theatersData = await theatersResponse.json();
                if (Array.isArray(theatersData.theaters)) {
                    this.renderTheatersChart(theatersData.theaters);
                }
            }
        } catch (error) {
            console.error('Error loading bookings:', error);
            this.showError('Failed to load bookings and theater data.');
        }
    }

    /**
     * Render revenue trend line chart
     * 
     * Shows daily revenue over 30 days as a smooth line chart
     * Features:
     * - Filled area under the line
     * - Formatted Y-axis with rupee symbol and K abbreviation
     * - Tooltip on hover
     * - Responsive and maintains aspect ratio
     * 
     * @param {Object} data - {dates: string[], revenues: number[]}
     */
    renderRevenueChart(data) {
        const ctx = document.getElementById('revenueChart');
        if (!ctx) return;
        
        // Validate chart data
        if (!data || !data.dates || !data.revenues || data.dates.length === 0) {
            console.warn('No revenue data to render');
            return;
        }
        
        // Destroy previous chart instance to prevent memory leaks
        if (this.charts.revenue) {
            this.charts.revenue.destroy();
        }

        try {
            // Create new line chart with gradient styling
            this.charts.revenue = new Chart(ctx.getContext('2d'), {
                type: 'line',
                data: {
                    // Format dates to 'Mon 10' format for readability
                    labels: data.dates.map(d => {
                        const date = new Date(d + 'T00:00:00');
                        return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' });
                    }),
                    datasets: [{
                        label: 'Revenue (₹)',
                        data: data.revenues.map(v => Math.max(0, v)),
                        borderColor: '#667eea',  // Line color
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',  // Fill color
                        fill: true,
                        tension: 0.4,  // Smooth curves
                        pointRadius: 4,  // Data point size
                        pointBackgroundColor: '#667eea',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointHoverRadius: 6,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    plugins: {
                        legend: { 
                            display: true, 
                            position: 'top',
                            labels: {
                                font: { size: 12, weight: '600' },
                                padding: 15,
                                usePointStyle: true,
                            }
                        },
                        filler: { propagate: true },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: { size: 12, weight: 'bold' },
                            bodyFont: { size: 11 },
                            cornerRadius: 6,
                            displayColors: true,
                            callbacks: {
                                label: (context) => {
                                    const value = context.parsed.y || 0;
                                    return 'Revenue: ₹' + value.toLocaleString('en-IN', { maximumFractionDigits: 0 });
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(0, 0, 0, 0.05)', drawBorder: false },
                            ticks: {
                                // Format large numbers with K abbreviation
                                callback: (v) => {
                                    if (v >= 1000) {
                                        return '₹' + (v / 1000).toFixed(0) + 'k';
                                    }
                                    return '₹' + v;
                                },
                                font: { size: 11 },
                                color: '#858796',
                                padding: 8,
                            }
                        },
                        x: {
                            grid: { display: false, drawBorder: false },
                            ticks: { 
                                font: { size: 11 },
                                color: '#858796',
                                padding: 8,
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error rendering revenue chart:', error);
            this.showError('Failed to render revenue chart.');
        }
    }

    /**
     * Render top movies bar chart
     * 
     * Shows top 5 movies by booking count as a horizontal bar chart
     * Green color highlighting top performers
     * 
     * @param {Array} movies - [{title, bookings}, ...]
     */
    renderMoviesChart(movies) {
        const ctx = document.getElementById('moviesChart');
        if (!ctx) return;
        
        // Validate movie data
        if (!Array.isArray(movies) || movies.length === 0) {
            console.warn('No movie data to render');
            return;
        }
        
        // Clean up previous instance
        if (this.charts.movies) {
            this.charts.movies.destroy();
        }

        try {
            // Create bar chart for top movies
            this.charts.movies = new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    // Display full movie titles
                    labels: movies.map(m => {
                        if (!m.title) return 'Unknown';
                        // Truncate to reasonable length for display
                        return m.title.length > 20 ? m.title.substring(0, 20) + '...' : m.title;
                    }),
                    datasets: [{
                        label: 'Bookings',
                        data: movies.map(m => Math.max(0, m.bookings || 0)),
                        backgroundColor: '#1cc88a',  // Green for positive metric
                        borderRadius: 6,
                        borderSkipped: false,
                        hoverBackgroundColor: '#17a66f',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',  // Horizontal bar chart
                    plugins: {
                        legend: { 
                            display: true, 
                            position: 'top',
                            labels: { 
                                font: { size: 12, weight: '600' }, 
                                padding: 15,
                                usePointStyle: true,
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            cornerRadius: 6,
                            callbacks: {
                                label: (context) => {
                                    return 'Bookings: ' + (context.parsed.x || 0).toLocaleString('en-IN');
                                }
                            }
                        }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            grid: { display: false, drawBorder: false },
                            ticks: { 
                                font: { size: 11 },
                                color: '#858796',
                            }
                        },
                        x: {
                            beginAtZero: true,
                            grid: { color: 'rgba(0, 0, 0, 0.05)', drawBorder: false },
                            ticks: { 
                                font: { size: 11 },
                                color: '#858796',
                                callback: (v) => (v || 0).toLocaleString('en-IN'),
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error rendering movies chart:', error);
            this.showError('Failed to render movies chart.');
        }
    }

    /**
     * Render top theaters bar chart
     * 
     * Shows top 5 theaters by revenue as a bar chart
     * Cyan/blue color for revenue metrics
     * 
     * @param {Array} theaters - [{name, bookings, revenue}, ...]
     */
    renderTheatersChart(theaters) {
        const ctx = document.getElementById('theatersChart');
        if (!ctx) return;
        
        // Validate theater data
        if (!Array.isArray(theaters) || theaters.length === 0) {
            console.warn('No theater data to render');
            return;
        }
        
        // Clean up previous instance
        if (this.charts.theaters) {
            this.charts.theaters.destroy();
        }

        try {
            // Create bar chart for top theaters
            this.charts.theaters = new Chart(ctx.getContext('2d'), {
                type: 'bar',
                data: {
                    // Display full theater names
                    labels: theaters.map(t => {
                        if (!t.name) return 'Unknown';
                        // Truncate to reasonable length for display
                        return t.name.length > 20 ? t.name.substring(0, 20) + '...' : t.name;
                    }),
                    datasets: [{
                        label: 'Revenue (₹)',
                        data: theaters.map(t => Math.max(0, t.revenue || 0)),
                        backgroundColor: '#36b9cc',  // Cyan for revenue
                        borderRadius: 6,
                        borderSkipped: false,
                        hoverBackgroundColor: '#2aa5ba',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',  // Horizontal bar chart
                    plugins: {
                        legend: { 
                            display: true, 
                            position: 'top',
                            labels: { 
                                font: { size: 12, weight: '600' }, 
                                padding: 15,
                                usePointStyle: true,
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            cornerRadius: 6,
                            callbacks: {
                                label: (context) => {
                                    const value = context.parsed.x || 0;
                                    return 'Revenue: ₹' + value.toLocaleString('en-IN', { maximumFractionDigits: 0 });
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { display: false, drawBorder: false },
                            ticks: { 
                                font: { size: 11 },
                                color: '#858796',
                            }
                        },
                        x: {
                            beginAtZero: true,
                            grid: { color: 'rgba(0, 0, 0, 0.05)', drawBorder: false },
                            ticks: {
                                font: { size: 11 },
                                color: '#858796',
                                callback: (v) => {
                                    if (v >= 1000) {
                                        return '₹' + (v / 1000).toFixed(0) + 'k';
                                    }
                                    return '₹' + v;
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error rendering theaters chart:', error);
            this.showError('Failed to render theaters chart.');
        }
    }

    renderBookingsTable(bookings) {
        const tbody = document.getElementById('bookingsTable');
        if (!tbody) return;
        
        if (!Array.isArray(bookings) || bookings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted"><em>No bookings found</em></td></tr>';
            return;
        }

        try {
            tbody.innerHTML = bookings.map(b => {
                // Validate booking object
                const user = this.escapeHtml(b.user || 'Unknown');
                const movie = this.escapeHtml((b.movie || 'Unknown').substring(0, 25));
                const amount = (b.amount || 0).toLocaleString('en-IN', { 
                    maximumFractionDigits: 2,
                    minimumFractionDigits: 0
                });
                
                return `
                    <tr>
                        <td><strong>${user}</strong></td>
                        <td title="${this.escapeHtml(b.movie || 'Unknown')}" style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            ${movie}
                        </td>
                        <td class="text-end">₹${amount}</td>
                    </tr>
                `;
            }).join('');
        } catch (error) {
            console.error('Error rendering bookings table:', error);
            tbody.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Error loading bookings</td></tr>';
        }
    }

    escapeHtml(text) {
        if (typeof text !== 'string') {
            return '';
        }
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new AdminDashboard();
});
