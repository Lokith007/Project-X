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
        card.className = 'bg-[#161b22] border border-[#30363d] rounded-lg p-4 hover:border-[#58a6ff] transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/10';

        // Mutual connections badge
        const mutualBadge = dev.mutual_count > 0 ? `
            <div class="flex items-center gap-1 px-2 py-1 bg-[#0d1117]/50 rounded-lg border border-[#21262d] text-xs">
                <i class="fa-solid fa-users text-[#58a6ff]"></i>
                <span class="text-[#7d8590]">${dev.mutual_count} mutual</span>
            </div>
        ` : '';

        // Coding style badge
        const codingStyleBadge = dev.coding_style ? `
            <div class="flex items-center gap-2 px-2 py-1 bg-[#0d1117]/30 rounded-lg border border-[#21262d]">
                <img src="/static/assets/coding-style-logo/${dev.coding_style.logo}" 
                     alt="${dev.coding_style.name}"
                     class="w-4 h-4">
                <span class="text-xs text-[#e6edf3]">${dev.coding_style.name}</span>
            </div>
        ` : '';

        // Follow button
        const followBtn = dev.is_following ? `
            <a href="javascript:void(0);" class="follow-btn px-4 text-center py-2 bg-[#262b34] text-white font-mono text-sm rounded-md hover:scale-[1.03] transition" data-user-id="${dev.id}">
                <span class="btn-text">&lt;Unfollow/&gt;</span>
            </a>
        ` : `
            <a href="javascript:void(0);" class="follow-btn px-4 text-center py-2 bg-[#6feb85] text-black font-mono text-sm rounded-md hover:scale-[1.03] transition" data-user-id="${dev.id}">
                <span class="btn-text">&lt;Follow/&gt;</span>
            </a>
        `;

        card.innerHTML = `
            <!-- Avatar & Info -->
            <div class="flex flex-col items-center text-center mb-3">
                <a href="/user-profile/${dev.username}/" class="mb-3">
                    <img src="${dev.avatar || '/static/user_profile_img/profile.jpg'}" 
                         alt="${dev.username}"
                         class="w-16 h-16 rounded-full border-2 border-[#30363d] hover:border-[#58a6ff] transition-colors object-cover">
                </a>
                
                <a href="/user-profile/${dev.username}/" 
                   class="font-semibold text-[#e6edf3] hover:text-[#58a6ff] transition-colors text-sm mb-1">
                    @${dev.username}
                </a>
                
                ${dev.full_name && dev.full_name !== dev.username ? `
                    <p class="text-xs text-[#7d8590]">${dev.full_name}</p>
                ` : ''}
                
                ${dev.location ? `
                    <p class="text-xs text-[#7d8590] mt-1">
                        <i class="fa-solid fa-location-dot text-[10px]"></i>
                        ${dev.location}
                    </p>
                ` : ''}
            </div>
            
            <!-- Bio -->
            ${dev.bio ? `
                <div class="mb-3">
                    <p class="text-xs text-[#a8b3cf] line-clamp-2">${dev.bio}</p>
                </div>
            ` : ''}
            
            <!-- Badges -->
            <div class="flex flex-wrap gap-2 mb-3 justify-center">
                ${mutualBadge}
                ${codingStyleBadge}
            </div>
            
            <!-- Follow Button -->
            <div class="mt-auto">
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
