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

function clickSound() {
      const sound = document.getElementById("clickSound");
      sound.currentTime = 0;
      sound.play();
}

//For Joining in projects
function toggleJoinRequest(projectId){
    $.ajax({
        url: `/collab-project/request-project-join/${projectId}/`,
        type: "POST",
        headers: {"X-CSRFToken":  getCSRFToken() },
        success: function(data){
            let btn = $("#joinProjectBtn");
            btn.text(data.requested ? "Cancel Request" : "Request to Join")
            
            btn.addClass("scale-110");
            setTimeout(() => btn.removeClass("scale-110"), 200);

            const helpDiv = $("#join_help_text_div");

            if(data.requested){
                // Apply success styles - dark theme
                helpDiv
                    .removeClass("bg-yellow-600/20 border-yellow-600 bg-red-600/20 border-red-600")
                    .addClass("bg-green-600/20 border-green-600")
                    .removeClass("border-l-yellow-500 border-l-red-500")
                    .addClass("border-l-green-500");

                helpDiv.find("i")
                    .removeClass("text-yellow-400 text-red-400")
                    .addClass("text-green-400");

                helpDiv.find("#join_help_text_div").html(
                    "Request sent successfully 🎉. Updation takes a few seconds."
                );

            } else {
                // Apply cancelled styles - dark theme
                helpDiv
                    .removeClass("bg-yellow-600/20 border-yellow-600 bg-green-600/20 border-green-600")
                    .addClass("bg-red-600/20 border-red-600")
                    .removeClass("border-l-yellow-500 border-l-green-500")
                    .addClass("border-l-red-500");

                helpDiv.find("i")
                    .removeClass("text-yellow-400 text-green-400")
                    .addClass("text-red-400");

                helpDiv.find("#join_help_text_div").html(
                    "Request cancelled. You can re-apply anytime!"
                );
                $("#show_status").hide();
            }
        },
        error: function(error) {
            console.error("Error:", error);
        }
    });
}

//For Creator accepting and rejecting request
function accept_or_reject_request(projectId, userId, action){
    $.ajax({
        url: `/collab-project/accept-or-reject-request/${projectId}/${userId}/`,
        type: "POST",
        data: { action: action },
        headers: {
            "X-CSRFToken": getCSRFToken()
        },
        success: function(data) {
            document.getElementById("clickSound").play();
            let userDiv = $(`#user_id_${userId}`);
            userDiv.next('hr').remove();  // remove <hr> after the div
            userDiv.fadeOut(300, () => {
                userDiv.remove();

                // If no pending users left, show the message above the removed div
                if (data.pending_count === 0) {
                     const messageDiv = $(`
                        <div class="text-sm text-gray-600 bg-green-50 border border-green-200 rounded-md px-4 py-3 mt-2 mb-2">
                                <i class="fa-solid fa-circle-check text-green-600 mr-2"></i>
                                All requests reviewed — nothing left to check!
                            </div>
                        `);
                        $('#parent_user_div').prepend(messageDiv);
                     }
            });

            $('#accepted_count').text(data.accepted_count);
            $('#pending_count').text(data.pending_count);
            $('#rejected_count').text(data.rejected_count);
        },
        error: function(err) {
            console.error("Failed:", err);
        }
    });
}


//Leave Project Team
function leaveProjectMembers(projectId){
    $.ajax({
        url: `/collab-project/leave-project-members/${projectId}/`,
        type: "POST",
        headers: {"X-CSRFToken":  getCSRFToken() },
        success: function(data){
            let btn = $("#joinProjectBtn");
            if (data.removed) {
                btn.prop("disabled", true);
                btn.text("Left Project!");
                btn.removeClass("bg-rose-700").addClass("bg-green-600");
                if (data.total_member !== undefined) {
                    $("#membercount").text(`${data.total_member}`);
                }
                $("#show_status").hide();
                const helpDiv = $("#join_help_text_div");
                helpDiv.find("#join_help_text_div").html(
                    "You’ve left the project 👋. Request again later if you're still interested."
                );
            } else if (data.error) {
                alert(data.error); // optional: show user-friendly message
            }
            btn.addClass("scale-110");
            setTimeout(() => btn.removeClass("scale-110"), 200);
        },
        error: function(error) {
            console.error("Error:", error);
        }
    });
}

// Project comment save
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
                alert(response.error || 'Something went wrong');
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
                    alert(response.error || "Something went wrong!");
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

// #Toggle like for project comment
$(document).ready(function() {
    $(document).on('click', '.comment-container', function() {
        let container = $(this);
        let commentId = container.data("comment-id");
        let heartIcon = container.find("i");
        let likeCountSpan = container.find("span");
        let actionUrl = `/collab-project/toggle_comment_like/${commentId}/`; 
        
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
        let actionUrl = `/collab-project/toggle_reply_like/${replyId}/`; 
        
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
    $(document).on("click", ".delete-project-comment", function () {
        var commentID = $(this).data("id");
        var form_type = $(this).data("type");
        var commentBox = $("#comment-" + commentID);
        
        $.ajax({
            url: "/delete-data/",  
            type: "POST",
            data: {
                'comment_id': commentID,
                'form_type': form_type,
                'csrfmiddlewaretoken': getCSRFToken(),
            },
            success: function (response) {
                if (response.success) {
                    commentBox.fadeOut(300, function () { $(this).remove(); });
                    $('#total_comments').text(response.comment_count);
                    if (response.comment_count === 0) {
                        $('#commentBox').html(`
                        <div class="text-xl bg-gradient-to-br from-green-600 to-green-900 text-white p-4 rounded-t-xl text-center mb-2"> <span class="text-white"  id='total_comments'>${response.comment_count}</span> Comments</div>
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
                        </div>`
                        );
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
    $(document).on("click", ".delete-reply-comment", function () {
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

document.addEventListener("DOMContentLoaded", function () {
    const loadBtn = document.getElementById("loadMoreBtn");
    if (!loadBtn) return;

    loadBtn.addEventListener("click", function () {
        const originalText = this.innerHTML;
        this.disabled = true;
        this.innerHTML = `<span class="loader inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></span> Loading...`;

        const lastId = this.dataset.lastId;
        const url = new URL(window.location.href);
        url.searchParams.set('last_id', lastId);

        fetch(url, {
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        })
        .then(res => res.json())
        .then(data => {
            document.getElementById("parent_user_div").insertAdjacentHTML("beforeend", data.html);
            if (data.has_more) {
                this.dataset.lastId = data.last_id;
                this.innerHTML = originalText;
                this.disabled = false;
            } else {
                this.remove(); // No more users to load
            }
        }).catch(() => {
            this.innerHTML = "Load More";
            this.disabled = false;
            alert("Something went wrong. Please try again.");
        });
    });
});
