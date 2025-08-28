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

function copyCurrentURL() {
    const currentURL = window.location.href;
    navigator.clipboard.writeText(currentURL)
        .then(() => {
            alert("🔗 Link copied successfully!");
        })
        .catch(err => {
            console.error("Failed to copy: ", err);
            alert("❌ Could not copy the link.");
        });
}

function copySnippet(sig) {
    const codeElement = document.getElementById(`code-snippet-${sig}`);
    const text = codeElement.innerText;
    navigator.clipboard.writeText(text).then(() => {
        alert('Snippet copied!');
    });
}

// Post option navbar Menu
document.addEventListener('DOMContentLoaded', () => {
    const popupTrigger = document.getElementById('popupTrigger');
    const postOptionTrigger = document.getElementById('postOptionTrigger');
    const popup = document.getElementById('popup');
    const postOption = document.getElementById('postOption'); // Fixed: Correct ID

    // Helper to toggle visibility
    const toggleElement = (element, showClass, hideClass) => {
        element.classList.toggle(showClass);
        element.classList.toggle(hideClass);
    };

    // Handle popup
    if (popupTrigger && popup) {
        popupTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleElement(popup, 'fixed', 'hidden');
            postOption?.classList.add('hidden'); // Hide postOption if open
            postOption?.classList.remove('absolute');

            if (!popup.classList.contains('hidden')) {
                const closeOnOutside = (event) => {
                    if (!popup.contains(event.target) && !popupTrigger.contains(event.target)) {
                        popup.classList.add('hidden');
                        popup.classList.remove('fixed');
                        document.removeEventListener('click', closeOnOutside);
                    }
                };
                document.addEventListener('click', closeOnOutside);
            }
        });
    }

    // Handle postOption
    if (postOptionTrigger && postOption) {
        postOptionTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleElement(postOption, 'absolute', 'hidden');
            popup?.classList.add('hidden'); // Hide popup if open
            popup?.classList.remove('fixed');

            if (!postOption.classList.contains('hidden')) {
                const closeOnOutside = (event) => {
                    if (!postOption.contains(event.target) && !postOptionTrigger.contains(event.target)) {
                        postOption.classList.add('hidden');
                        postOption.classList.remove('absolute');
                        document.removeEventListener('click', closeOnOutside);
                    }
                };
                document.addEventListener('click', closeOnOutside);

                // Add click listeners to each option inside postOption to close the menu
                postOption.querySelectorAll('.cursor-pointer').forEach(option => {
                    option.addEventListener('click', () => {
                        postOption.classList.add('hidden');
                        postOption.classList.remove('absolute');
                    });
                });
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const trigger = document.getElementById('exploreTrigger');
    const dropdown = document.getElementById('allExplore');

    if (trigger && dropdown) {
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('hidden');
            dropdown.classList.toggle('flex');

            if (!dropdown.classList.contains('hidden')) {
                const closeOnOutside = (event) => {
                    if (!trigger.contains(event.target) && !dropdown.contains(event.target)) {
                        dropdown.classList.add('hidden');
                        dropdown.classList.remove('flex');
                        document.removeEventListener('click', closeOnOutside);
                    }
                };
                document.addEventListener('click', closeOnOutside);
            }
        });
    }
});


const openFilter = () => {
    if (window.screen.width < 1024) {
        const filterElement = document.getElementById('filterElement');
        const openFilterParent = document.getElementById('openFilterParent');
        filterElement.classList.toggle('fixed')
        filterElement.classList.add('flex')
        filterElement.classList.remove('hidden')
        openFilterParent.classList.remove('hidden')
    }
}

const closeFilter = () => {
    const filterElement = document.getElementById('filterElement');
    const openFilterParent = document.getElementById('openFilterParent');
    filterElement.classList.remove('fixed')
    filterElement.classList.add('hidden')
    openFilterParent.classList.add('hidden')
}


// for handling reply btn action
const handleReply = (commentId, name) => {
    const textArea = document.getElementById('commentTextArea');
    const parentCommentId = document.getElementById('parentCommentId');
    textArea.focus();
    textArea.placeholder = `Replying to ${name}`;
    parentCommentId.value = commentId;
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.replyBtn').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 
                    'center'
                });
                target.focus();
            }
        });
    });
});


const goTo = (url) => {
    window.open('https://' + url, '_blank');
}


// For post menu
$(document).ready(function() {
    $(document).on('click', '[id^="postMenuTrigger-"]', function(e) {
        e.stopPropagation();
        const trigger = this;
        const postId = trigger.id.split('-')[1];
        const menu = document.getElementById(`postMenu-${postId}`);

        if (trigger && menu) {
            // Close other open menus
            document.querySelectorAll('[id^="postMenu-"]').forEach(otherMenu => {
                if (otherMenu !== menu) {
                    otherMenu.classList.add('hidden');
                    otherMenu.classList.remove('flex');
                }
            });

            // Toggle current menu
            menu.classList.toggle('hidden');
            menu.classList.toggle('flex');

            if (!menu.classList.contains('hidden')) {
                const closeOnOutside = (event) => {
                    if (!menu.contains(event.target) && !trigger.contains(event.target)) {
                        menu.classList.add('hidden');
                        menu.classList.remove('flex');
                        document.removeEventListener('click', closeOnOutside);
                    }
                };
                document.addEventListener('click', closeOnOutside);
            }

            // Close menu when clicking delete link (if no redirect)
            menu.querySelector('a').addEventListener('click', () => {
                menu.classList.add('hidden');
                menu.classList.remove('flex');
            });
        } else {
            console.log(`Processing trigger: postMenuTrigger-${postId}, menu: ${menu ? 'found' : 'not found'}`);
        }
    });

    // Log the number of initial triggers for debugging
    const initialTriggers = document.querySelectorAll('[id^="postMenuTrigger-"]');
    console.log(`Found ${initialTriggers.length} post menu triggers on page load`);
});

const viewProfile = () => {
    const entireSection = document.getElementById('entireSection')
    const zoomProfile = document.getElementById('zoomProfile')
    entireSection.classList.toggle('blur')
    zoomProfile.classList.toggle('flex')
    zoomProfile.classList.toggle('hidden')
}

const closeProfile = () => {
    const entireSection = document.getElementById('entireSection')
    const zoomProfile = document.getElementById('zoomProfile')
    entireSection.classList.remove('blur')
    zoomProfile.classList.add('hidden')
    zoomProfile.classList.remove('flex')
}

// resize post
const postImgContainer = document.getElementById('postImgContainer')
const resizePost = (size) => {
    const postImg = document.getElementById('postImg')
    postImg.classList.add('object-cover')
    postImg.classList.remove('object-contain')
    if (size) {
        postImgContainer.classList.add('aspect-video')
        postImgContainer.classList.remove('aspect-square')
    }
    else {
        postImgContainer.classList.add('aspect-square')
        postImgContainer.classList.remove('aspect-video')
    }
}

// set original post image
const setImgOriginal = () => {
    const postImg = document.getElementById('postImg')
    postImg.classList.add('object-contain')
    postImg.classList.remove('object-cover')
    postImgContainer.classList.remove('aspect-square')
    postImgContainer.classList.add('aspect-video')
}

//Get aspect ratio for userpost
function setAspectRatio(ratio){
    document.getElementById('aspectRatioInput').value = ratio
}

// upload post
const uploadPost = document.getElementById('uploadPost')
const uploadPostContainer = document.getElementById('uploadPostContainer')
const uploadPostLabel = document.getElementById('uploadPostLabel')

uploadPost.addEventListener('change', (event) => {
    postImgContainer.classList.remove('object-contain')
    postImgContainer.classList.remove('aspect-square')
    postImgContainer.classList.add('aspect-video')
    const postImg = document.getElementById('postImg')

    const file = event.target.files[0]
    if (file) {
        const reader = new FileReader()
        reader.onload = () => {
            postImg.classList.remove('hidden')
            postImg.classList.add('block')
            postImg.src = reader.result
            uploadPostContainer.classList.add('hidden')
            uploadPostLabel.classList.remove('hidden')
        }
        reader.readAsDataURL(file)
    }
})

// opening create post div function for org and user
const openPost = (type = 'user', value = 'user-post') => {
    const entireSection = document.getElementById('entireSection')
    const createPost = document.getElementById('createPost')
    const actionInput = document.getElementById('postActionInput')
    if (actionInput) {
        actionInput.value = value;
    }
    entireSection.classList.add('blur-md')
    createPost.classList.remove('hidden')
    createPost.classList.add('flex')
}

// closing create post div function
const closePost = () => {
    const entireSection = document.getElementById('entireSection')
    const createPost = document.getElementById('createPost')
    entireSection.classList.remove('blur-md')
    createPost.classList.add('hidden')
    createPost.classList.remove('flex')
}

//Disable submit btn for post, when loading
$(document).ready(function () {
    $('#createPost form').on('submit', function () {
        const submitBtn = $('#postSubmitButton');
        submitBtn.prop("disabled", true);
        submitBtn.html(`<i class="fa-solid fa-spinner fa-spin mr-2"></i> ${submitBtn.val() || 'Posting...'}`);
    });
});


//Toggle for follow or unfollow users
$(document).ready(function () {
    $(document).on('click', '.follow-btn', function() {
        let btn = $(this);
        let userId = btn.data("user-id");
        let actionUrl;
        let isFollowing = btn.find(".btn-text").text().trim().includes("Unfollow");

        if (isFollowing) {
            actionUrl = `/unfollow/${userId}/`;
        }else {
            actionUrl = `/follow/${userId}/`;   // URL for follow
        }

        $.ajax({
            url: actionUrl,
            type: "POST",
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.status === "followed") {
                    btn.find(".btn-text").text("<Unfollow/>");
                    btn.removeClass("bg-[#6feb85] text-black");
                    btn.addClass("bg-[#262b34] text-white")
                    document.getElementById("clickSound").play();
                } 
                else if (response.status === "unfollowed") {
                    btn.find(".btn-text").text("<Follow/>");
                    btn.removeClass('bg-[#262b34] text-white')
                    btn.addClass("bg-[#6feb85] text-black")
                }

                $(`.followers-count`).text(`${response.followers_count}`);
                $(`.following-count`).text(`${response.following_count}`);
            },
            error: function (xhr) {
                console.error("Error:", xhr.responseText);
            }
        });
    });
}); 

//Follow Toggle for organization
$(document).ready(function() {
    $('.follow-toggle-org').click(function(e) {
        e.preventDefault();
        const button = $(this);
        const orgId = button.data('org-id');
        const type = button.data('type');
        console.log(type);
        const isFollow = button.text().trim() === 'Follow';
        if (isFollow) {
            actionUrl =  `/organization/${orgId}/follow/`
        }else {
            actionUrl = `/organization/${orgId}/unfollow/`   // URL for follow
        }
        
        $.ajax({
            url: actionUrl,
            method: 'POST',
            headers: {
                "X-CSRFToken": getCSRFToken()
            },
            success: function(data) {
                if (data.status === 'followed') {
                    // Toggle button appearance
                    button.text('Unfollow')
                    button.removeClass("bg-[#6feb85]");
                    button.addClass("bg-[#464646] text-white");
                   
                } else if (data.status === 'unfollowed') {
                    button.text('Follow');
                    button.removeClass('bg-[#464646] text-white');
                    button.addClass("bg-[#6feb85] text-black");
                }
                $(`#followers-count-${orgId}`).text(`${data.followers_count} Followers`);
            },
            error: function(xhr) {
                alert(xhr.responseJSON?.message || 'An error occurred');
            }
        });
    });
});

// #Toggle like for post
$(document).ready(function() {
    $(document).on('click', '.like-container', function() {
        let container = $(this);
        let postId = container.data("post-id");
        let heartIcon = container.find("i");
        let likeCountSpan = container.find("span");
        let actionUrl = `/toggle_like/${postId}/`; 
        
        $.ajax({
            url: actionUrl,
            type: "POST",
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function(response) {
                // Update the heart icon's style based on like status
                if (response.liked) {
                    heartIcon.addClass("text-[#6feb85]");
                } else {
                    heartIcon.removeClass("text-[#6feb85]");
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

//For toggling the comments
document.addEventListener('click', function(e) {
    if (e.target.closest('.commentBtn')) {
        const btn = e.target.closest('.commentBtn');
        const allBtns = document.querySelectorAll('.commentBtn');
        const allSections = document.querySelectorAll('.commentsSection');

        allBtns.forEach((b, i) => {
            if (b === btn) {
                if (allSections[i].classList.contains('hidden')) {
                    allSections[i].classList.remove('hidden');
                } else {
                    allSections[i].classList.add('hidden');
                }
            }
        });
    }
});

//For saving post comments
$(document).ready(function(){
    $(document).on("submit", ".postCommentForm", function(event){
        event.preventDefault();
        var form = $(this);
        var commentText = form.find("input[name='comment']").val();

        if(commentText.trim() === "") {
            alert("Comment cannot be empty!");
            return;
        }

        
        var postId = form.data("post-id");
        var csrftoken = form.find("input[name='csrfmiddlewaretoken']").val();

        $.ajax({
            url: form.attr("action"),
            type: 'POST',
            data: {
                'comment': commentText,
                'post_id': postId,
                'csrfmiddlewaretoken': csrftoken
            },
            success: function(response) {
                var commentHTML = "<div class='flex items-start space-x-2 mt-2' id='postComment" + response.comment_id + "'>" +
                                        "<a href='/user-profile/" + response.username + "'/>" +
                                           "<img src='" + response.profile_image_url + "' alt='User' class='w-8 h-8 rounded-sm object-cover'>" +
                                        "</a>" +
                                        "<div class='bg-[#1a1f26] border border-gray-700 p-2 rounded-lg w-full flex flex-row items-center justify-between'>" +
                                            "<div>" +
                                                "<a href='/user_profile/" + response.username + "/' class='text-sm font-semibold -mt-2'>" + response.username + "</a>" +
                                                "<p class='text-sm mt-2'>" + response.comment + "</p>" +
                                            "</div>" +
                                            "<button class='deletePostComment' data-comment-id='" + response.comment_id + "'>" +
                                            "<img src='/static/assets/trash-bin.svg' class='h-6 w-6 cursor-pointer'></img>" +
                                            "</button>" +
                                        "</div>" +
                                    "</div>";

                $("#postCommentContainer" + postId).prepend(commentHTML);
                // Clear the comment text input
                form.find("input[name='comment']").val('');
                // Update the comment count if available
                $("#postCommentCount" + postId).text(response.comments_count);
            },  error: function(xhr, errmsg, err) {
                console.error("Error saving comment: " + errmsg);
            }
        });
    });
});

//for deleting posts comments
$(document).ready(function(){
    $(document).on("click", ".deletePostComment", function(event){
        console.log(true)
        event.preventDefault();
        var commentId = $(this).data("comment-id");
        var csrftoken = $("input[name='csrfmiddlewaretoken']").val(); // Ensure your CSRF token is accessible

        $.ajax({
            url: '/delete-post-comment/' + commentId + '/',  // Ensure this URL matches your Django URL conf
            type: 'DELETE',
            headers: {
                "X-CSRFToken": csrftoken  // Pass the CSRF token in the header
            },
            success: function(response) {

                $("#postComment" + commentId).remove();
                $("#postCommentCount" + response.post_id).text(response.comments_count);
            },
            error: function(xhr, errmsg, err) {
                console.error("Error deleting comment: " + errmsg);
            }
        });
    });
});


// Post save Toggle
$(document).ready(function() {
    $(document).on('click', '.bookmark-container', function() {
        let container = $(this);
        let postId = container.data("post-id");
        let bookmarkIcon = container.find("i");
        let actionUrl = `/toggle_post_save/${postId}/`; 

        $.ajax({
            url: actionUrl,
            type: "POST",
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function(response) {
                if (response.saved) {
                    bookmarkIcon.addClass("text-[#6feb85]");
                } else {
                    bookmarkIcon.removeClass("text-[#6feb85]");
                }
                // Update the like count in the span
                // likeCountSpan.text(response.total_likes);
            },
            error: function(xhr) {
                console.error("Error toggling save:", xhr.responseText);
            }
        });
    });
});

// Project Save Toggle
$(document).ready(function() {
    $(document).on('click', '.bookmark-container-project', function() {
        let container = $(this);
        let projectId = container.data("project-id");
        let bookmarkIcon = container.find("i");
        let actionUrl = `/collab-project/toggle_project_save/${projectId}/`; 

        $.ajax({
            url: actionUrl,
            type: "POST",
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function(response) {
                // Update the heart icon's style based on like status
                if (response.saved) {
                    bookmarkIcon.addClass("text-[#6feb85]");
                } else {
                    bookmarkIcon.removeClass("text-[#6feb85]");
                }
            },
            error: function(xhr) {
                console.error("Error toggling save:", xhr.responseText);
            }
        });
    });
});

//event save toggle
$(document).ready(function() {
    $(document).on('click', '.bookmark-container-event', function() {
        let container = $(this);
        let eventId = container.data("event-id");
        let bookmarkIcon = container.find("i");
        let actionUrl = `/events/toggle_event_save/${eventId}/`; 

        $.ajax({
            url: actionUrl,
            type: "POST",
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function(response) {
                // Update the heart icon's style based on like status
                if (response.saved) {
                    bookmarkIcon.addClass("text-[#6feb85]");
                } else {
                    bookmarkIcon.removeClass("text-[#6feb85]");
                }
            },
            error: function(xhr) {
                console.error("Error toggling save:", xhr.responseText);
            }
        });
    });
});

function fetchNotificationCount() {
    $.get("/notifications/count/", function(data) {
        let count = data.unread_count;
        if (count > 0) {
            $("#notification-badge").text(count).show();
        } else {
            $("#notification-badge").hide();
        }
    });
}

$(document).ready(function() {
    fetchNotificationCount();
    setInterval(fetchNotificationCount, 10000);  // Check every 10 seconds
});


// For toasting
function toast(message = "Something happened!", type = "default", duration = 3000) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");

    // Type-based color classes
    let color = "bg-gray-800 text-white";
    if (type === "success") color = "bg-green-600 text-white";
    if (type === "error") color = "bg-red-600 text-white";
    if (type === "warn") color = "bg-yellow-400 text-black";

    // Apply base Tailwind styling and custom entry class
    toast.className = `
        px-4 py-2 rounded-md shadow-lg font-mono text-sm
        ${color} toast-animate-in
    `;

    toast.innerText = message;
    container.appendChild(toast);

    // Add exit animation before removal
    setTimeout(() => {
        toast.classList.remove("toast-animate-in");
        toast.classList.add("toast-animate-out");
    }, duration);

    setTimeout(() => {
        toast.remove();
    }, duration + 600);
}

//for reward + emoji drop
function triggerDevmateReward(message, emojis) {
    const defaultEmojis = ["🎉", "✨", "🔥", "🚀", "🏆", "🥳"];
    if (!emojis || emojis.length === 0) {
        emojis = defaultEmojis;
    }

    const banner = document.getElementById('devmate-reward-banner');
    const messageSpan = document.getElementById('devmate-reward-message');
    const emojiContainer = document.getElementById('emoji-drop-container');

    messageSpan.textContent = message;
    banner.classList.remove('hidden');
    banner.classList.add('devmate-reward-anim-show');

    // Drop Emojis
    for (let i = 0; i < 60; i++) {
        const emoji = document.createElement('div');
        emoji.classList.add('emoji-drop');
        emoji.style.left = Math.random() * 100 + "vw";
        emoji.style.animationDuration = (2 + Math.random()) + "s";
        emoji.innerText = emojis[Math.floor(Math.random() * emojis.length)];
        emojiContainer.appendChild(emoji);

        setTimeout(() => emoji.remove(), 4000);
    }

    // Auto-hide banner
    setTimeout(() => {
        banner.classList.remove('devmate-reward-anim-show');
        setTimeout(() => banner.classList.add('hidden'), 500);
    }, 6000);
}