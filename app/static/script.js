// ==========================================
// Modern SaaS UI Scripts
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');
    let overlay = document.getElementById('sidebarOverlay');

    // Create overlay if it doesn't exist
    if (!overlay && sidebar) {
        overlay = document.createElement('div');
        overlay.id = 'sidebarOverlay';
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
    }

    if (mobileMenuBtn && sidebar && overlay) {
        function toggleSidebar() {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('open');
        }

        mobileMenuBtn.addEventListener('click', toggleSidebar);
        overlay.addEventListener('click', toggleSidebar);
    }

    // 2. Form Submissions - Subtle loading state
    const forms = document.querySelectorAll("form");
    forms.forEach(f => {
        f.addEventListener("submit", (e) => {
            const submitBtn = f.querySelector('button[type="submit"]');
            if (submitBtn) {
                // Prevent double submission visually
                submitBtn.style.opacity = '0.7';
                submitBtn.style.pointerEvents = 'none';
                
                // If the button has text, we can append a spinner or dot
                if (!submitBtn.dataset.originalText) {
                    submitBtn.dataset.originalText = submitBtn.textContent;
                    submitBtn.textContent = 'Processing...';
                }
            }
        });
    });

    // 3. Confirm Deletion
    const deleteForms = document.querySelectorAll('form[action*="/delete"]');
    deleteForms.forEach(f => {
        f.onsubmit = () => {
            return confirm('Are you sure you want to delete this? This action cannot be undone.');
        };
    });
});