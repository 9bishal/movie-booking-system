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
     * Get CSRF token from cookie
     * Required for Django POST requests
     */
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Get fetch headers with CSRF token for API calls
     */
    getFetchHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCsrfToken() || '',
        };
    }

    /**
     * Initialize dashboard by loading all data and setting up filters
     * 
     * Called automatically on page load via DOMContentLoaded event.
     * Loads stats, revenue data, bookings, and theaters in parallel.
     * Sets up filter event listeners.
     */
    async init() {
        if (this.isLoading) return;
        this.isLoading = true;
        
        try {
            // Setup filter event listeners
            this.setupFilters();
            
            // Load all data concurrently
            await Promise.all([
                this.loadStats(),
                this.loadRevenue(),
                this.loadBookings()
            ]);
        } catch (error) {
            console.error('Error initializing dashboard:', error);
            this.showError('Failed to load dashboard data. Please refresh the page.');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Setup filter event listeners
     * Attaches handlers to date range, movie, and theater filters
     */
    setupFilters() {
        const self = this;
        const applyFiltersBtn = document.getElementById('applyFiltersBtn');
        const resetFiltersBtn = document.getElementById('resetFiltersBtn');
        const dateFromEl = document.getElementById('dateFrom');
        const dateToEl = document.getElementById('dateTo');
        const movieEl = document.getElementById('movieFilter');
        const theaterEl = document.getElementById('theaterFilter');
        
        // Bind apply filters button
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Apply filters button clicked');
                self.applyFilters();
            });
        } else {
            console.warn('Apply filters button not found');
        }
        
        // Bind reset filters button
        if (resetFiltersBtn) {
            resetFiltersBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Reset filters button clicked');
                self.resetFilters();
            });
        } else {
            console.warn('Reset filters button not found');
        }
        
        // Allow Enter key to apply filters
        if (dateFromEl) {
            dateFromEl.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    self.applyFilters();
                }
            });
        }
        
        if (dateToEl) {
            dateToEl.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    self.applyFilters();
                }
            });
        }
        
        // Auto-apply filters when dropdown changes
        if (movieEl) {
            movieEl.addEventListener('change', function() {
                self.applyFilters();
            });
        }
        
        if (theaterEl) {
            theaterEl.addEventListener('change', function() {
                self.applyFilters();
            });
        }
        
        // Load movies and theaters into dropdowns
        this.loadFilterDropdowns();
        
        console.log('Filter event listeners setup complete');
    }

    /**
     * Apply filters and reload dashboard
     */
    async applyFilters() {
        const dateFrom = document.getElementById('dateFrom')?.value || '';
        const dateTo = document.getElementById('dateTo')?.value || '';
        const movieId = document.getElementById('movieFilter')?.value || '';
        const theaterId = document.getElementById('theaterFilter')?.value || '';
        
        console.log('Applying filters:', { dateFrom, dateTo, movieId, theaterId });
        
        if (this.isLoading) {
            console.warn('Dashboard is already loading, please wait...');
            return;
        }
        this.isLoading = true;
        
        try {
            console.log('Loading stats, revenue, and bookings with filters...');
            await Promise.all([
                this.loadStats(dateFrom, dateTo, movieId, theaterId),
                this.loadRevenue(dateFrom, dateTo, movieId, theaterId),
                this.loadBookings(dateFrom, dateTo, movieId, theaterId)
            ]);
            console.log('All dashboard data loaded successfully');
        } catch (error) {
            console.error('Error applying filters:', error);
            this.showError('Failed to apply filters. Please try again.');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Reset all filters and reload dashboard
     */
    async resetFilters() {
        const dateFromEl = document.getElementById('dateFrom');
        const dateToEl = document.getElementById('dateTo');
        const movieEl = document.getElementById('movieFilter');
        const theaterEl = document.getElementById('theaterFilter');
        
        if (dateFromEl) dateFromEl.value = '';
        if (dateToEl) dateToEl.value = '';
        if (movieEl) movieEl.value = '';
        if (theaterEl) theaterEl.value = '';
        
        console.log('Filters reset, reloading data...');
        await this.applyFilters();
    }

    /**
     * Load and display summary statistics
     * 
     * Fetches: Total revenue, today's revenue, total bookings, today's bookings
     * Updates stat cards with formatted currency and numbers
     * 
     * API: GET /custom-admin/api/stats/
     * Returns: {total_revenue, today_revenue, total_bookings, today_bookings}
     * 
     * @param {string} dateFrom - Start date filter (YYYY-MM-DD)
     * @param {string} dateTo - End date filter (YYYY-MM-DD)
     * @param {string} movieId - Movie ID filter
     * @param {string} theaterId - Theater ID filter
     */
    async loadStats(dateFrom = '', dateTo = '', movieId = '', theaterId = '') {
        try {
            const params = new URLSearchParams();
            if (dateFrom) params.append('date_from', dateFrom);
            if (dateTo) params.append('date_to', dateTo);
            if (movieId) params.append('movie_id', movieId);
            if (theaterId) params.append('theater_id', theaterId);
            
            const queryString = params.toString() ? `?${params.toString()}` : '';
            const url = `${this.apiBaseUrl}/stats/${queryString}`;
            console.log('Fetching stats from:', url);
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Stats API error: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Stats data received:', data);
            
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
     * 
     * @param {string} dateFrom - Start date filter (YYYY-MM-DD)
     * @param {string} dateTo - End date filter (YYYY-MM-DD)
     * @param {string} movieId - Movie ID filter
     * @param {string} theaterId - Theater ID filter
     */
    async loadRevenue(dateFrom = '', dateTo = '', movieId = '', theaterId = '') {
        try {
            const params = new URLSearchParams();
            params.append('days', '30');
            if (dateFrom) params.append('date_from', dateFrom);
            if (dateTo) params.append('date_to', dateTo);
            if (movieId) params.append('movie_id', movieId);
            if (theaterId) params.append('theater_id', theaterId);
            
            const queryString = params.toString() ? `?${params.toString()}` : '';
            const url = `${this.apiBaseUrl}/revenue/${queryString}`;
            console.log('Fetching revenue from:', url);
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Revenue API error: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Revenue data received:', data);
            
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
     * 
     * @param {string} dateFrom - Start date filter (YYYY-MM-DD)
     * @param {string} dateTo - End date filter (YYYY-MM-DD)
     * @param {string} movieId - Movie ID filter
     * @param {string} theaterId - Theater ID filter
     */
    async loadBookings(dateFrom = '', dateTo = '', movieId = '', theaterId = '') {
        try {
            const params = new URLSearchParams();
            if (dateFrom) params.append('date_from', dateFrom);
            if (dateTo) params.append('date_to', dateTo);
            if (movieId) params.append('movie_id', movieId);
            if (theaterId) params.append('theater_id', theaterId);
            
            const queryString = params.toString() ? `?${params.toString()}` : '';
            const bookingsUrl = `${this.apiBaseUrl}/bookings/${queryString}`;
            const theatersUrl = `${this.apiBaseUrl}/theaters/${queryString}`;
            
            console.log('Fetching bookings from:', bookingsUrl);
            console.log('Fetching theaters from:', theatersUrl);
            
            const [bookingsResponse, theatersResponse] = await Promise.all([
                fetch(bookingsUrl),
                fetch(theatersUrl)
            ]);
            
            if (!bookingsResponse.ok) {
                throw new Error(`Bookings API error: ${bookingsResponse.status}`);
            }
            
            const bookingsData = await bookingsResponse.json();
            console.log('Bookings data received:', bookingsData);
            
            // Validate bookings data
            if (!Array.isArray(bookingsData.movies) || !Array.isArray(bookingsData.bookings)) {
                throw new Error('Invalid bookings data format');
            }
            
            // Render top movies bar chart
            console.log('About to render movies chart with:', bookingsData.movies);
            this.renderMoviesChart(bookingsData.movies);
            // Populate recent bookings table
            this.renderBookingsTable(bookingsData.bookings);
            
            // Handle theaters data if available
            if (theatersResponse.ok) {
                const theatersData = await theatersResponse.json();
                console.log('Theaters data received:', theatersData);
                if (Array.isArray(theatersData.theaters)) {
                    console.log('About to render theaters chart with:', theatersData.theaters);
                    this.renderTheatersChart(theatersData.theaters);
                } else {
                    console.warn('Theaters data is not an array:', theatersData);
                }
            } else {
                console.error('Theaters API failed:', theatersResponse.status);
            }
        } catch (error) {
            console.error('Error loading bookings:', error);
            this.showError('Failed to load bookings and theater data.');
        }
    }

    /**
     * Load movies and theaters into filter dropdowns
     */
    async loadFilterDropdowns() {
        console.log('[loadFilterDropdowns] Starting...');
        
        // Load movies list
        console.log('[loadFilterDropdowns] Fetching movies...');
        const moviesUrl = `${this.apiBaseUrl}/movies-list/`;
        console.log('[loadFilterDropdowns] Movies URL:', moviesUrl);
        
        try {
            const moviesResponse = await fetch(moviesUrl);
            console.log('[loadFilterDropdowns] Movies response received, status:', moviesResponse.status);
            
            if (moviesResponse.ok) {
                const moviesData = await moviesResponse.json();
                console.log('[loadFilterDropdowns] Movies data:', moviesData);
                
                const movieSelect = document.getElementById('movieFilter');
                console.log('[loadFilterDropdowns] Movie select element:', movieSelect);
                
                if (movieSelect && Array.isArray(moviesData.movies)) {
                    console.log('[loadFilterDropdowns] Found', moviesData.movies.length, 'movies');
                    
                    moviesData.movies.forEach(movie => {
                        console.log('[loadFilterDropdowns] Creating option for movie:', movie);
                        const option = document.createElement('option');
                        option.value = String(movie.id);
                        option.textContent = String(movie.title);
                        movieSelect.appendChild(option);
                        console.log('[loadFilterDropdowns] Option added for:', movie.title);
                    });
                    
                    console.log('[loadFilterDropdowns] Finished adding movies. Total options:', movieSelect.options.length);
                }
            } else {
                console.error('[loadFilterDropdowns] Movies API returned status:', moviesResponse.status);
            }
        } catch (error) {
            console.error('[loadFilterDropdowns] Error fetching movies:', error);
        }

        // Load theaters list
        console.log('[loadFilterDropdowns] Fetching theaters...');
        const theatersUrl = `${this.apiBaseUrl}/theaters-list/`;
        console.log('[loadFilterDropdowns] Theaters URL:', theatersUrl);
        
        try {
            const theatersResponse = await fetch(theatersUrl);
            console.log('[loadFilterDropdowns] Theaters response received, status:', theatersResponse.status);
            
            if (theatersResponse.ok) {
                const theatersData = await theatersResponse.json();
                console.log('[loadFilterDropdowns] Theaters data:', theatersData);
                
                const theaterSelect = document.getElementById('theaterFilter');
                console.log('[loadFilterDropdowns] Theater select element:', theaterSelect);
                
                if (theaterSelect && Array.isArray(theatersData.theaters)) {
                    console.log('[loadFilterDropdowns] Found', theatersData.theaters.length, 'theaters');
                    
                    theatersData.theaters.forEach(theater => {
                        console.log('[loadFilterDropdowns] Creating option for theater:', theater);
                        const option = document.createElement('option');
                        option.value = String(theater.id);
                        option.textContent = String(theater.name);
                        theaterSelect.appendChild(option);
                        console.log('[loadFilterDropdowns] Option added for:', theater.name);
                    });
                    
                    console.log('[loadFilterDropdowns] Finished adding theaters. Total options:', theaterSelect.options.length);
                }
            } else {
                console.error('[loadFilterDropdowns] Theaters API returned status:', theatersResponse.status);
            }
        } catch (error) {
            console.error('[loadFilterDropdowns] Error fetching theaters:', error);
        }
        
        console.log('[loadFilterDropdowns] Complete');
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
        
        // Destroy previous chart instance
        if (this.charts.revenue) {
            this.charts.revenue.destroy();
        }
        
        // Validate chart data
        if (!data || !data.dates || !data.revenues || data.dates.length === 0) {
            console.warn('No revenue data to render');
            // Create empty chart instead of showing message
            this.createEmptyChart('revenue', ctx, 'line', 'Revenue (₹)');
            return;
        }
        
        // Even if all zeros, still show the chart
        const hasData = data.revenues.some(v => v > 0);
        if (!hasData) {
            console.warn('No revenue data (all zeros) - showing empty chart');
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
        
        // Clean up previous instance
        if (this.charts.movies) {
            this.charts.movies.destroy();
        }
        
        // Validate movie data
        if (!Array.isArray(movies) || movies.length === 0) {
            console.warn('No movie data to render');
            this.createEmptyChart('movies', ctx, 'bar', 'Bookings');
            return;
        }
        
        // Even if all zeros, still show the chart
        const hasData = movies.some(m => m.bookings > 0);
        if (!hasData) {
            console.warn('No movie data (all zeros) - showing empty chart');
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
        
        // Clean up previous instance
        if (this.charts.theaters) {
            this.charts.theaters.destroy();
        }
        
        // Validate theater data
        if (!Array.isArray(theaters) || theaters.length === 0) {
            console.warn('No theater data to render');
            this.createEmptyChart('theaters', ctx, 'bar', 'Revenue (₹)');
            return;
        }
        
        // Even if all zeros, still show the chart
        const hasData = theaters.some(t => t.revenue > 0);
        if (!hasData) {
            console.warn('No theater data (all zeros) - showing empty chart');
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

    /**
     * Create an empty chart with "No data" message
     */
    createEmptyChart(chartName, ctx, type, label) {
        const config = {
            type: type,
            data: {
                labels: ['No Data'],
                datasets: [{
                    label: label,
                    data: [0],
                    backgroundColor: '#e0e0e0',
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: type === 'bar' ? 'y' : 'x',
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { display: false },
                        ticks: { display: type !== 'bar' }
                    },
                    x: {
                        beginAtZero: true,
                        grid: { display: false },
                        ticks: { display: type === 'bar' }
                    }
                }
            }
        };
        
        this.charts[chartName] = new Chart(ctx.getContext('2d'), config);
    }
}

// Initialize dashboard when DOM is ready OR immediately if already loaded
function initializeDashboard() {
    new AdminDashboard();
}

if (document.readyState === 'loading') {
    // DOM is still loading, wait for it
    document.addEventListener('DOMContentLoaded', initializeDashboard);
} else {
    // DOM is already ready, initialize immediately
    initializeDashboard();
}
//