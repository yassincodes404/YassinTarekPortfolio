/**
 * Admin panel utility functions — HTMX, toast notifications
 */

// ── Toast notifications ──────────────────────────────────
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ── HTMX event listeners ─────────────────────────────────
document.addEventListener('htmx:afterRequest', function(event) {
    if (event.detail.xhr.status >= 200 && event.detail.xhr.status < 300) {
        // Success handled by individual hx-on handlers
    } else {
        showToast('An error occurred', 'error');
    }
});

// ── Copy to clipboard ────────────────────────────────────
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    });
}

// ── Confirmation dialogs ─────────────────────────────────
document.addEventListener('htmx:confirm', function(event) {
    if (event.detail.question) {
        event.preventDefault();
        if (confirm(event.detail.question)) {
            event.detail.issueRequest();
        }
    }
});
