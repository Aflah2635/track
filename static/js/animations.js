document.addEventListener('DOMContentLoaded', () => {
    // Page load transition
    document.body.classList.add('page-transition');
    
    // Initialize animations
    initAnimations();
});

// Re-initialize on HTMX content swap
document.addEventListener('htmx:afterSwap', (event) => {
    initAnimations();
    // Optional: Add specific animation for swapped content if needed
    if (event.target.classList.contains('page-transition-target')) {
        event.target.classList.add('animate-fade-in');
    }
});

function initAnimations() {
    // Auto-dismiss notifications
    const notifications = document.querySelectorAll('.notification-toast');
    notifications.forEach((note, index) => {
        // Skip if already processing
        if (note.hasAttribute('data-animating')) return;
        
        note.setAttribute('data-animating', 'true');
        note.style.animationDelay = `${index * 0.1}s`;
        note.classList.add('notification-slide-in');

        // Auto dismiss after 4 seconds
        setTimeout(() => {
            note.classList.add('notification-slide-out');
            note.addEventListener('transitionend', () => {
                note.remove();
            });
        }, 4000 + (index * 500));
    });

    // Add click effect to primary buttons if they don't have it
    const buttons = document.querySelectorAll('.btn-primary, .btn-secondary, button[type="submit"], a.btn, .btn');
    buttons.forEach(btn => {
        if (!btn.classList.contains('btn-click-effect')) {
            btn.classList.add('btn-click-effect');
        }
    });

    // Add hover effects to cards if missing (for dynamically loaded content)
    const cards = document.querySelectorAll('.glass-card:not(.hover-scale)');
    cards.forEach(card => {
        // Only add if it's meant to be interactive or we generally want it
        if (card.closest('a') || card.classList.contains('cursor-pointer')) {
            card.classList.add('hover-scale');
        }
    });
}
