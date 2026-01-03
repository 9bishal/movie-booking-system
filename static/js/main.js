/**
 * Global JavaScript for MovieBooking
 * Contains common utility functions for Wishlist, Toasts, and Cookies.
 */

// --- Wishlist AJAX Logic ---

/**
 * Toggles a movie in the user's wishlist via AJAX
 * @param {HTMLElement} button - The button element clicked
 * @param {string|number} movieId - The ID of the movie
 */
async function toggleWishlist(button, movieId) {
    const btn = button instanceof HTMLElement ? button : (event ? event.currentTarget : null);
    if (!btn) return;
    const icon = btn.querySelector('i');
    const label = btn.querySelector('span.fw-bold');
    const csrftoken = getCookie('csrftoken');
    
    try {
        const response = await fetch(`/${movieId}/wishlist/toggle/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        const data = await response.json();
        
        if (data.success) {
            if (data.action === 'added') {
                if(icon) {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                }
                if(label) label.textContent = 'In Watchlist';
                btn.classList.remove('btn-outline-danger');
                btn.classList.add('btn-danger', 'text-white');
                showToast(`Added to watchlist`, 'success');
            } else {
                if(icon) {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                }
                if(label) label.textContent = 'Watch Later';
                btn.classList.remove('btn-danger', 'text-white');
                btn.classList.add('btn-outline-danger');
                showToast('Removed from watchlist', 'info');
            }
        }
    } catch (error) {
        console.error('Wishlist error:', error);
        showToast('Please login to use watchlist', 'danger');
    }
}

/**
 * Toggles a movie in the user's interest list via AJAX
 */
async function toggleInterest(button, movieId) {
    const btn = button instanceof HTMLElement ? button : (event ? event.currentTarget : null);
    if (!btn) return;
    const icon = btn.querySelector('i');
    const label = btn.querySelector('span.fw-bold');
    const csrftoken = getCookie('csrftoken');
    
    try {
        const response = await fetch(`/${movieId}/interest/toggle/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        const data = await response.json();
        
        if (data.success) {
            if (data.action === 'added') {
                if(icon) {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                }
                if(label) label.textContent = 'Interested';
                btn.classList.remove('btn-outline-success');
                btn.classList.add('btn-success');
                showToast(`Interested!`, 'success');
            } else {
                if(icon) {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                }
                if(label) label.textContent = 'Interested?';
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-success');
            }
            
            // Update counts if they exist on the page
            const countElems = document.querySelectorAll(`.interest-count-${movieId}`);
            countElems.forEach(el => {
                el.textContent = data.interest_count;
            });
        }
    } catch (error) {
        console.error('Interest toggle error:', error);
        showToast('Please login to show interest', 'danger');
    }
}

/**
 * Displays a temporary Bootstrap notification
 * @param {string} message - The message to display
 * @param {string} type - Bootstrap color type (success, danger, info, warning)
 */
function showToast(message, type = 'info') {
    // Remove existing toasts to prevent stacking too many
    document.querySelectorAll('.toast-container-custom').forEach(t => t.remove());

    const toastContainer = document.createElement('div');
    toastContainer.className = `toast-container-custom position-fixed bottom-0 end-0 p-3`;
    toastContainer.style.zIndex = '9999';
    
    toastContainer.innerHTML = `
        <div class="toast align-items-center text-white bg-${type} border-0 show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-info-circle'} me-2"></i> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    document.body.appendChild(toastContainer);
    
    // Auto remove after 4 seconds
    setTimeout(() => {
        if (toastContainer && toastContainer.parentNode) {
            toastContainer.parentNode.removeChild(toastContainer);
        }
    }, 4000);
}

/**
 * Helper to retrieve CSRF token from cookies
 * @param {string} name - The name of the cookie to retrieve
 */
function getCookie(name) {
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
