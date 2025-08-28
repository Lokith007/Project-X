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

// show or hide replies
function toggleReplies(commentId, btnElement, replyCount) {
    const $replies = $(`#replies-for-${commentId}`);
    const $btn = $(btnElement);

    if ($replies.is(":visible")) {
        $replies.hide();
        $btn.html(`<i class="fa-solid fa-chevron-down text-xs"></i> Show Replies (${replyCount})`);
    } else {
        $replies.css("display", "flex");
        $btn.html(`<i class="fa-solid fa-chevron-up text-xs"></i> Hide Replies`);
    }
}

function toggleReplyForm(commentId) {
    $(`#reply-form-${commentId}`).slideToggle(150);
}

// Event comment save
$(document).ready(function () {
    $('#commentForm').on('submit', function (e) {
        e.preventDefault();

        const form = $(this);
        const url = form.attr('action');
        const data = form.serialize();

        $.post(url, data, function (response) {
            if (response.success) {
                // Add comment to top
                $('#commentList').prepend(response.comment_html);
                $('#noCommentSVG').hide();

                // Clear textarea
                $('#commentTextArea').val('');

                // Update total comments
                $('#total_comments').text(response.total);
            } else {
                alert(response.error || 'Please log in to continue.');
            }
        });
    });
});

// Reply comment save
$(document).ready(function () {
    $(document).on("submit", ".reply-form", function (e) {
        e.preventDefault();
        const $form = $(this);
        const commentId = $form.data("comment-id");
        const repliesContainer = $(`#replies-for-${commentId}`);
        const submitBtn = $form.find("button[type='submit']");
        const originalBtnHTML = submitBtn.html();
        submitBtn.prop("disabled", true).html(`<i class="fa-solid fa-spinner fa-spin"></i> Posting...`);

        $.ajax({
            url: $form.attr("action"),
            method: "POST",
            headers: { "X-CSRFToken": getCSRFToken() },
            data: $form.serialize(),
            success: function (response) {
                if (response.success) {
                    repliesContainer.prepend(response.reply_html);
                    $form[0].reset();
                    repliesContainer.slideDown(200);
                    $('#total_comments').text(response.total_comments);
                    $(`#show_reply_count_${commentId}`).text(response.show_replies_count);
                } else {
                    alert(response.error || "Please log in to continue.");
                }
            },
            error: function () {
                alert("Server error. Try again.");
            },
            complete: function () {
                submitBtn.prop("disabled", false).html(originalBtnHTML);
            }
        });
    });
});


// #Toggle like for event comment
$(document).ready(function() {
    $(document).on('click', '.comment-container', function() {
        let container = $(this);
        let commentId = container.data("comment-id");
        let heartIcon = container.find("i");
        let likeCountSpan = container.find("span");
        let actionUrl = `/events/toggle_comment_like/${commentId}/`; 
        
        $.ajax({
            url: actionUrl,
            type: "POST",
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function(response) {
                // Update the thumb up icon's style based on like status
                if (response.liked) {
                    heartIcon.addClass("text-[#53d26a]");
                } else {
                    heartIcon.removeClass("text-[#53d26a]");
                }
                // Update the like count in the span
                likeCountSpan.text(response.total_likes);
            },
            error: function(xhr) {
                console.error("Error toggling like:", xhr.responseText);
            }
        });
    });
});

// #Toggle like for reply comment
$(document).ready(function() {
    $(document).on('click', '.reply-container', function() {
        let container = $(this);
        let replyId = container.data("reply-id");
        let heartIcon = container.find("i");
        let likeCountSpan = container.find("span");
        let actionUrl = `/events/toggle_reply_like/${replyId}/`; 
        
        $.ajax({
            url: actionUrl,
            type: "POST",
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function(response) {
                // Update the thumb up icon's style based on like status
                if (response.liked) {
                    heartIcon.addClass("text-[#53d26a]");
                } else {
                    heartIcon.removeClass("text-[#53d26a]");
                }
                // Update the like count in the span
                likeCountSpan.text(response.total_likes);
            },
            error: function(xhr) {
                console.error("Error toggling like:", xhr.responseText);
            }
        });
    });
});

// #Delete Comment
$(document).ready(function () {
    $(document).on("click", ".delete-event-comment", function () {
        var commentID = $(this).data("id");
        var form_type = $(this).data("type");
        var commentBox = $("#comment-" + commentID);

        $.ajax({
            url: "/delete-data/", 
            type: "POST",
            data: {
                'comment_id': commentID,
                'form_type': form_type,
                'csrfmiddlewaretoken':  getCSRFToken(),
            },
            success: function (response) {
                if (response.success) {
                    commentBox.fadeOut(300, function () { $(this).remove(); });
                        $('#total_comments').text(response.comment_count);
                        if (response.comment_count === 0) {
                            $('#commentBox').html(`
                            <div class="text-xl bg-gradient-to-br from-green-600 to-green-900 text-white p-4 rounded-t-xl text-center mb-2"> <span class="text-white" id='total_comments'>${response.comment_count}</span> Comments</div>
                            <div id="commentList" class="flex flex-col gap-y-4 px-4 mt-2">
                                <div class='flex flex-col gap-y-8 px-3' id='noCommentSVG'>
                                    <div class="flex flex-col items-center justify-center py-8">
                                        <div class="w-20 h-20 mb-4 bg-gradient-to-br from-green-500/20 to-green-700/20 rounded-full flex items-center justify-center">
                                            <i class="fas fa-comments text-2xl text-green-400"></i>
                                        </div>
                                        <p class='text-center text-lg text-gray-300 pb-5'>No comments yet...</p>
                                        <div class="w-12 h-0.5 bg-gradient-to-r from-green-500 to-green-700 rounded-full"></div>
                                    </div>
                                </div>
                            </div>
                        `);
                        }
                } else {
                    alert("Error deleting comment.");
                }
            },
            error: function () {
                alert("Something went wrong!");
            }
        });
    });
});

//Delete reply comment
$(document).ready(function () {
    $(document).on("click", ".delete-event-reply", function () {
        var replyID = $(this).data("id");
        var form_type = $(this).data("type");
        var commentBox = $("#reply-" + replyID);

        $.ajax({
            url: "/delete-data/", 
            type: "POST",
            data: {
                'comment_id': replyID,
                'form_type': form_type,
                'csrfmiddlewaretoken': getCSRFToken(),
            },
            success: function (response) {
                if (response.success) {
                    commentBox.fadeOut(300, function () { $(this).remove(); });
                    $('#total_comments').text(response.comment_count);
                } else {
                    alert("Error deleting comment.");
                }
            },
            error: function () {
                alert("Something went wrong!");
            }
        });
    });
});