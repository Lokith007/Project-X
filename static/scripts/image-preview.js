/**
 * Log Image Preview Modal
 * Handles fullscreen image preview functionality
 */

function previewImage(imageUrl) {
    const modal = document.getElementById('imagePreviewModal');
    const img = document.getElementById('modalPreviewImage');

    if (!modal || !img) {
        console.error('Image preview modal elements not found');
        return;
    }

    img.src = imageUrl;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden';
}

function closeImagePreview() {
    const modal = document.getElementById('imagePreviewModal');

    if (!modal) return;

    modal.classList.add('hidden');
    modal.classList.remove('flex');
    document.body.style.overflow = 'auto';
}

// Initialize event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    // Close on Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeImagePreview();
        }
    });
});
