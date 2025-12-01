/**
 * Profile Banner Logic
 * Handles modal interactions and AJAX updates for the profile banner.
 */

document.addEventListener('DOMContentLoaded', function () {
    // Event delegation for banner selection
    const bannerModal = document.getElementById('bannerModal');
    if (!bannerModal) return;

    // Close modal when clicking outside
    bannerModal.addEventListener('click', function (e) {
        if (e.target === this) {
            closeBannerModal();
        }
    });
});

function openBannerModal() {
    const modal = document.getElementById('bannerModal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function closeBannerModal() {
    const modal = document.getElementById('bannerModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

function selectBanner(bannerName) {
    // Optimistic UI update
    const bannerImg = document.getElementById('profileBanner');
    if (bannerImg) {
        const baseUrl = bannerImg.getAttribute('data-banner-base-url');
        if (baseUrl) {
            bannerImg.src = baseUrl + bannerName;
        } else {
            console.error('Base URL for banners not found');
        }
    }

    closeBannerModal();

    // Send request
    const formData = new FormData();
    formData.append('banner', bannerName);

    // Get CSRF token from cookie or input
    const csrfToken = getCookie('csrftoken');
    if (!csrfToken) {
        console.error('CSRF token not found');
        alert('Security token missing. Please refresh the page.');
        location.reload();
        return;
    }
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch('/update-banner/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('Banner updated successfully');
            } else {
                console.error('Failed to update banner:', data.error);
                alert('Failed to update banner: ' + (data.error || 'Unknown error'));
                location.reload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while updating the banner. Please check your connection.');
            location.reload();
        });
}

// Helper to get cookie (standard Django way)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
