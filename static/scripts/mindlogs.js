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
