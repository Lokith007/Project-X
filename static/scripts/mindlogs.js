function getCSRFToken() {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith("csrftoken=")) {
        cookieValue = cookie.substring("csrftoken=".length);
        break;
      }
    }
  }
  return cookieValue;
}

//For Deleting logs - Works for both prefetched and dynamically loaded logs
document.addEventListener("DOMContentLoaded", function () {
  // Use event delegation on document for dynamic content
  $(document).on('click', '.delete-log-btn', function (e) {
    e.preventDefault();
    const button = $(this);
    const sig = button.data('log-id'); // Read from data-log-id attribute

    if (!sig) {
      console.error('No log signature found');
      alert('Error: Cannot identify the log to delete.');
      return;
    }

    const logCard = button.closest('.bg-\\[\\#12161d\\]'); // Find parent log card

    if (!confirm("Are you sure you want to delete this log?")) return;

    $.ajax({
      type: "POST",
      url: `/logs/delete-log/${sig}/`,
      headers: {
        "X-CSRFToken": getCSRFToken(),
      },
      success: function (response) {
        if (response.success) {
          logCard.fadeOut(400, function () {
            $(this).remove();
          });
          // Show success message (optional)
          console.log("Log deleted successfully!");
        } else {
          alert("Failed to delete the log.");
        }
      },
      error: function (xhr) {
        if (xhr.status === 403) {
          alert("Unauthorized: You can only delete your own logs.");
        } else if (xhr.status === 404) {
          alert("Log not found.");
        } else {
          alert("An error occurred. Please try again.");
        }
      }
    });
  });
});


//for log entry (code snippet and image)
function handle_log_ImageUpload(event) {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      document.getElementById('imagePreview').src = e.target.result;
      document.getElementById('imagePreviewContainer').classList.remove('hidden');
    };
    reader.readAsDataURL(file);
  }
}

function remove_log_Image() {
  document.getElementById('snapshotInput').value = "";
  document.getElementById('imagePreviewContainer').classList.add('hidden');
}

function toggleCodeSnippet() {
  const container = document.getElementById('codeSnippetContainer');
  container.classList.toggle('hidden');
}

function toggleLinkInput() {
  const container = document.getElementById('linkInputContainer');
  container.classList.toggle('hidden');
}


/**
 * Cursor-Based AJAX Load More Logs for User Profile Page
 */
document.addEventListener("DOMContentLoaded", function () {
  // Use event delegation on document for dynamic content
  $(document).on('click', '#load-more-profile-logs', function () {
    const btn = $(this);
    const username = btn.data('username');
    const cursor = btn.data('cursor');

    // Show loading state
    const originalText = btn.html();
    btn.html('<i class="fa fa-spinner fa-spin"></i> Loading...');
    btn.prop('disabled', true);

    $.ajax({
      url: `/logs/load-more-profile-logs/${username}/`,
      type: 'GET',
      data: { cursor: cursor },
      success: function (response) {
        if (response.logs_html && response.logs_html.trim() !== '') {
          // Append new logs to container
          $('#log-container').append(response.logs_html);

          // Update cursor for next load
          if (response.cursor) {
            btn.data('cursor', response.cursor);
          }

          // If no more logs, hide the button with smooth animation
          if (!response.has_next) {
            btn.parent().fadeOut(300, function () {
              $(this).remove();
            });
          } else {
            // Restore button
            btn.html(originalText);
            btn.prop('disabled', false);
          }
        } else {
          // No more logs
          btn.parent().fadeOut(300, function () {
            $(this).remove();
          });
        }
      },
      error: function (xhr, status, error) {
        console.error('Error loading more logs:', error);
        console.error('Response:', xhr.responseText);
        btn.html(originalText);
        btn.prop('disabled', false);

        // Show user-friendly error message
        const errorMsg = $('<div class="text-red-400 text-xs mt-2 text-center">Failed to load logs. Please try again.</div>');
        btn.parent().append(errorMsg);
        setTimeout(() => errorMsg.fadeOut(300, function () { $(this).remove(); }), 3000);
      }
    });
  });
});

/**
 * Toggle reaction picker visibility
 */
function toggleReactionPicker(sig) {
  const picker = $(`#picker-${sig}`);
  const isHidden = picker.hasClass('hidden');

  // Close all pickers and remove listeners
  $('.reaction-picker').addClass('hidden');
  $(document).off('click.reactionPicker');

  if (isHidden) {
    picker.removeClass('hidden');

    // Delay attachment to avoid catching the current click
    setTimeout(() => {
      $(document).on('click.reactionPicker', function (e) {
        // If clicked outside the picker
        if (!$(e.target).closest(`#picker-${sig}`).length) {
          picker.addClass('hidden');
          $(document).off('click.reactionPicker');
        }
      });
    }, 0);
  }
}

/**
 * Toggle reaction on a log
 */
function toggleReaction(sig, emoji) {
  // Close picker if open and remove listener
  $(`#picker-${sig}`).addClass('hidden');
  $(document).off('click.reactionPicker');

  $.ajax({
    type: "POST",
    url: `/logs/reaction/${sig}/`,
    data: {
      'emoji': emoji,
      'csrfmiddlewaretoken': getCSRFToken()
    },
    success: function (response) {
      // Update UI based on response
      const container = $(`#reactions-${sig}`);

      // We need to update specific emoji button in the active list
      // Since we are now using separate buttons for each emoji in the list

      // Iterate through all 4 supported emojis to update their state
      ['❤️', '🚀', '💡', '😢'].forEach(e => {
        const count = response.counts[e] || 0;
        let btn = container.find(`.reaction-btn[data-emoji="${e}"]`);

        if (count > 0) {
          // If button doesn't exist (was hidden), we might need to show it
          // But in our template we render all and hide them.
          btn.removeClass('hidden');
          btn.find('.count').text(count);

          // Update style based on user reaction
          if (response.user_reaction === e) {
            btn.removeClass('bg-[#0d1117] text-gray-500 border border-[#21262d] hover:border-gray-600 hover:text-gray-300')
              .addClass('bg-blue-500/10 text-blue-400 border-blue-500/30');
          } else {
            btn.removeClass('bg-blue-500/10 text-blue-400 border-blue-500/30')
              .addClass('bg-[#0d1117] text-gray-500 border border-[#21262d] hover:border-gray-600 hover:text-gray-300');
          }
        } else {
          // Hide button if count is 0
          btn.addClass('hidden');
        }
      });
    },
    error: function (xhr) {
      console.error('Error toggling reaction:', xhr.responseText);
    }
  });
}

// Make functions globally available
window.toggleReaction = toggleReaction;
window.toggleReactionPicker = toggleReactionPicker;
