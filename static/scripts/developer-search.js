/**
 * Developer Search - Real-time search with fuzzy matching and network ranking
 */

document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('developer-search-input');
    const searchResults = document.getElementById('search-results');
    const searchResultsContainer = document.getElementById('search-results-container');
    const searchLoading = document.getElementById('search-loading');
    const searchEmptyState = document.getElementById('search-empty-state');
    const emptyStateMessage = document.getElementById('empty-state-message');
    const resultsCount = document.getElementById('search-results-count');
    const clearSearchBtn = document.getElementById('clear-search');

    let debounceTimer;
    let currentQuery = '';

    // Search input handler with debouncing
    searchInput.addEventListener('input', function (e) {
        const query = e.target.value.trim();
        currentQuery = query;

        // Clear previous timeout
        clearTimeout(debounceTimer);

        // Hide results if query is empty
        if (!query) {
            hideResults();
            return;
        }

        // Show loading
        searchLoading.classList.remove('hidden');

        // Debounce API call (300ms)
        debounceTimer = setTimeout(() => {
            performSearch(query);
        }, 300);
    });

    // Clear search button
    clearSearchBtn.addEventListener('click', function () {
        searchInput.value = '';
        currentQuery = '';
        hideResults();
        searchInput.focus();
    });

    // Perform search via API
    async function performSearch(query) {
        try {
            const response = await fetch(`/api/search-developers/?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            searchLoading.classList.add('hidden');

            // Check if query is still current (user hasn't typed more)
            if (query !== currentQuery) {
                return;
            }

            if (data.results && data.results.length > 0) {
                displayResults(data.results, data.count);
            } else {
                showEmptyState(data.message || 'No developers found');
            }
        } catch (error) {
            console.error('Search error:', error);
            searchLoading.classList.add('hidden');
            showEmptyState('An error occurred. Please try again.');
        }
    }

    // Display search results
    function displayResults(results, count) {
        searchEmptyState.classList.add('hidden');
        searchResultsContainer.classList.remove('hidden');

        // Update count
        resultsCount.textContent = `${count} developer${count !== 1 ? 's' : ''} found`;

        // Clear previous results
        searchResults.innerHTML = '';

        // Render each result
        results.forEach(dev => {
            const card = createResultCard(dev);
            searchResults.appendChild(card);
        });
    }

    // Create result card
    function createResultCard(dev) {
        const card = document.createElement('div');
        card.className = 'group bg-[#0d1117] border border-[#30363d] rounded-xl p-2 py-4 pt-8 transition-all duration-200 hover:border-[#8b949e] hover:shadow-xl hover:shadow-[#000000]/20 flex flex-col items-center relative overflow-hidden';

        // Top Badge Content
        let badgeContent = '';
        if (dev.mutual_count > 0) {
            badgeContent = `
                <div class="absolute top-0 left-0 w-full bg-[#161b22] border-b border-[#30363d] py-1.5 px-3 flex items-center justify-center gap-2">
                    <i class="fa-solid fa-users text-[#58a6ff] text-[10px]"></i>
                    <span class="text-[10px] font-medium text-[#c9d1d9] truncate max-w-[90%]">${dev.mutual_count} mutual connection${dev.mutual_count !== 1 ? 's' : ''}</span>
                </div>
            `;
        } else {
            // Fallback badge for consistency or empty spacer
            badgeContent = `
                <div class="absolute top-0 left-0 w-full bg-[#161b22] border-b border-[#30363d] py-1.5 px-3 flex items-center justify-center gap-2">
                    <i class="fa-solid fa-code text-[#8b949e] text-[10px]"></i>
                    <span class="text-[10px] font-medium text-[#c9d1d9]">Developer</span>
                </div>
            `;
        }

        // Coding style badge
        const codingStyleBadge = dev.coding_style ? `
            <div class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-[#161b22] border border-[#30363d]" title="Coding Style: ${dev.coding_style.name}">
                <img src="/static/assets/coding-style-logo/${dev.coding_style.logo}" 
                     alt="${dev.coding_style.name}"
                     class="w-3.5 h-3.5 opacity-80 group-hover:opacity-100 transition-opacity">
                <span class="text-[10px] text-[#c9d1d9] font-medium">${dev.coding_style.name}</span>
            </div>
        ` : '';

        // Location badge
        const locationBadge = dev.location ? `
            <div class="flex items-center gap-1.5 px-2 py-1 rounded-full bg-[#161b22] border border-[#30363d]" title="${dev.location}">
                <i class="fa-solid fa-location-dot text-[10px] text-[#8b949e]"></i>
                <span class="text-[10px] text-[#c9d1d9] truncate max-w-[60px]">${dev.location.split(',')[0]}</span>
            </div>
        ` : '';

        // Follow button
        const followBtn = dev.is_following ? `
            <button onclick="toggleFollowSearch('${dev.id}', this)" 
                    class="w-full py-2 px-4 bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] border border-[#30363d] rounded-lg transition-all duration-200 text-xs font-medium shadow-sm hover:shadow">
                Unfollow
            </button>
        ` : `
            <button onclick="toggleFollowSearch('${dev.id}', this)" 
                    class="w-full py-2 px-4 bg-[#238636] hover:bg-[#2ea043] text-white border border-[rgba(240,246,252,0.1)] rounded-lg transition-all duration-200 text-xs font-bold shadow-md hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0">
                Follow
            </button>
        `;

        // Following indicator
        const followingIndicator = dev.is_following ? `
            <div class="absolute -bottom-1 -right-1 bg-[#238636] text-white text-xs w-6 h-6 flex items-center justify-center rounded-full border-[3px] border-[#0d1117] shadow-sm">
                <i class="fa-solid fa-check"></i>
            </div>
        ` : '';

        card.innerHTML = `
            ${badgeContent}
            
            <!-- Avatar & Info -->
            <div class="flex flex-col items-center text-center mb-3 mt-2">
                <a href="/user-profile/${dev.username}/" class="mb-3 relative group-hover:scale-105 transition-transform duration-300">
                    <img src="${dev.avatar || '/static/user_profile_img/profile.jpg'}" 
                         alt="${dev.username}"
                         class="w-20 h-20 rounded-full border-2 border-[#30363d] group-hover:border-[#8b949e] transition-colors object-cover bg-[#161b22] shadow-md">
                    ${followingIndicator}
                </a>
                
                <div class="text-center mb-3 w-full px-2">
                    <a href="/user-profile/${dev.username}/" 
                       class="block font-bold text-[#e6edf3] hover:text-[#58a6ff] transition-colors text-base truncate mb-0.5">
                        ${dev.full_name || dev.username}
                    </a>
                    <a href="/user-profile/${dev.username}/" 
                       class="block text-xs text-[#8b949e] hover:text-[#58a6ff] transition-colors truncate font-mono">
                        @${dev.username}
                    </a>
                </div>
            </div>
            
            <!-- Badges -->
            <div class="flex items-center justify-center gap-2 mb-4 w-full px-2">
                ${codingStyleBadge}
                ${locationBadge}
            </div>
            
            <!-- Follow Button -->
            <div class="w-full mt-auto px-2">
                ${followBtn}
            </div>
        `;

        return card;
    }

    // Show empty state
    function showEmptyState(message) {
        searchResultsContainer.classList.add('hidden');
        searchEmptyState.classList.remove('hidden');
        emptyStateMessage.textContent = message;
    }

    // Hide all results
    function hideResults() {
        searchResultsContainer.classList.add('hidden');
        searchEmptyState.classList.add('hidden');
        searchLoading.classList.add('hidden');
    }
});

// Toggle follow function (global scope for onclick)
async function toggleFollowSearch(userId, button) {
    const isFollowing = button.textContent.trim() === 'Unfollow';
    const originalContent = button.innerHTML;
    const originalClasses = button.className;

    // Optimistic UI update
    button.disabled = true;
    button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

    try {
        const url = isFollowing ? `/unfollow/${userId}/` : `/follow/${userId}/`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            // Toggle state
            if (isFollowing) {
                // Now not following
                button.textContent = 'Follow';
                button.className = 'w-full py-2 px-4 bg-[#238636] hover:bg-[#2ea043] text-white border border-[rgba(240,246,252,0.1)] rounded-lg transition-all duration-200 text-xs font-bold shadow-md hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0';

                // Remove checkmark if exists
                const card = button.closest('.group');
                const checkmark = card.querySelector('.fa-check')?.parentElement;
                if (checkmark) checkmark.remove();

            } else {
                // Now following
                button.textContent = 'Unfollow';
                button.className = 'w-full py-2 px-4 bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] border border-[#30363d] rounded-lg transition-all duration-200 text-xs font-medium shadow-sm hover:shadow';

                // Add checkmark
                const avatarLink = button.closest('.group').querySelector('a.relative');
                if (avatarLink && !avatarLink.querySelector('.fa-check')) {
                    const checkmark = document.createElement('div');
                    checkmark.className = 'absolute -bottom-1 -right-1 bg-[#238636] text-white text-xs w-6 h-6 flex items-center justify-center rounded-full border-[3px] border-[#0d1117] shadow-sm';
                    checkmark.innerHTML = '<i class="fa-solid fa-check"></i>';
                    avatarLink.appendChild(checkmark);
                }
            }
        } else {
            throw new Error('Action failed');
        }
    } catch (error) {
        console.error('Follow error:', error);
        button.innerHTML = originalContent;
        button.className = originalClasses;
        alert('Failed to update follow status. Please try again.');
    } finally {
        button.disabled = false;
    }
}

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
