// User Authentication & Floating Profile Widget Script
// Included identically across all submodules to persist the login state

document.addEventListener('DOMContentLoaded', () => {
    // Helper to determine root prefix for logout redirection
    const path = window.location.pathname.toLowerCase();
    let rootPrefix = '../';
    if (path.includes('/aarohan_1/login.html') || path.includes('/aarohan_1/register.html')) {
        rootPrefix = './';
    } else if (path.includes('/aarohan_1/home_page/index.html')) {
        rootPrefix = '../../';
    }

    // Export a globally available logout function for native buttons
    window.handleNativeLogout = function () {
        if (confirm("Are you sure you want to log out?")) {
            localStorage.removeItem('currentUser');
            localStorage.removeItem('isAdmin');
            localStorage.removeItem('adminDetails');
            // Provide visual feedback before reloading
            document.body.style.opacity = '0.5';
            window.location.href = rootPrefix + 'login.html';
        }
    };

    // Check if user is logged in
    const currentUserStr = localStorage.getItem('currentUser');

    if (!currentUserStr) {
        console.log("No active user session found in localStorage.");
        return;
    }

    const currentUser = JSON.parse(currentUserStr);

    // Make currentUser globally accessible for native UI
    window.currentUser = currentUser;

    // Auto-populate native profile elements if they exist in the DOM
    setTimeout(() => {
        const titleNames = document.querySelectorAll('.native-profile-name');
        const titleOccs = document.querySelectorAll('.native-profile-occ');
        const avatars = document.querySelectorAll('.native-profile-avatar');

        const firstName = currentUser.name ? currentUser.name.split(' ')[0] : 'User';
        const initial = currentUser.name ? currentUser.name.charAt(0).toUpperCase() : 'U';
        const role = currentUser.occupation || 'User';

        titleNames.forEach(el => el.innerText = firstName);
        titleOccs.forEach(el => el.innerText = role);
        avatars.forEach(el => el.innerText = initial);
    }, 100);

    // --- Autofill Integration ---
    // Automatically fill forms across all modules without overriding user intent.
    setTimeout(() => {
        // Robust query selectors looking for standard ids, names, and placeholders
        const nameFields = document.querySelectorAll('input[id*="name" i], input[id*="fullName" i], input[placeholder*="name" i], input[name*="name" i]');
        const mobileFields = document.querySelectorAll('input[id*="mobile" i], input[id*="phone" i], input[placeholder*="mobile" i], input[name*="phone" i], input[type="tel"]');
        const emailFields = document.querySelectorAll('input[id*="email" i], input[type="email"], input[placeholder*="email" i]');

        // Only autofill if the field currently is empty.
        nameFields.forEach(f => { if (!f.value && currentUser.name) f.value = currentUser.name; });
        mobileFields.forEach(f => { if (!f.value && currentUser.mobile) f.value = currentUser.mobile; });
        emailFields.forEach(f => { if (!f.value && currentUser.email && currentUser.email !== 'ఇవ్వలేదు') f.value = currentUser.email; });
    }, 300); // Small delay to allow any custom module scripts to render their forms fully
});

// ====== POINT 4: UNIVERSAL 3D HOVER PHYSICS ON CARDS ======
function applyUniversal3DTiltEffect() {
    // Select cards across the entire platform that should have the 3D effect
    // Targeting all the varying card schemas across modules (Youth, Transport, Farmers, Govt)
    const cards = document.querySelectorAll('.feature-card, .glass-panel, .card, .dashboard-card, .glass-card, .farmer-card, .job-card, .course-card, .scheme-card, .bg-white.rounded-lg, .bg-gray-800.rounded-lg, .hover\\:scale-105');

    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            // Calculate rotation based on mouse position (gentle max 8-10 deg tilt)
            const rotateX = ((y - centerY) / centerY) * -8;
            const rotateY = ((x - centerX) / centerX) * 8;

            card.style.transform = `perspective(1000px) scale(1.02) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
            card.style.transition = 'none'; // remove transition for smooth real-time tracking
            card.style.zIndex = '10'; // Keep it elevated over peers

            // Render beautiful subtle dynamic glare lighting effect that follows mouse
            card.style.boxShadow = `${-rotateY}px ${rotateX}px 25px rgba(255,255,255,0.15), 0 10px 30px rgba(0,0,0,0.3)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = `perspective(1000px) scale(1) rotateX(0deg) rotateY(0deg)`;
            card.style.transition = 'transform 0.5s cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.5s ease-out';
            card.style.zIndex = '1';
            card.style.boxShadow = '';
        });
    });
}

// Apply effect on DOM load across any module that links auth.js
document.addEventListener('DOMContentLoaded', () => {
    applyUniversal3DTiltEffect();
    // Re-apply after short delay for dynamically injected content (like react/api populated cards)
    setTimeout(applyUniversal3DTiltEffect, 1000);
});


