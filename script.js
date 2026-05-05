// ===== Language State =====
let currentLang = 'en';

// ===== Navigation =====
function navigateTo(page) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    
    // Show target page
    const targetPage = document.getElementById('page-' + page);
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    // Update nav active state
    document.querySelectorAll('.nav a').forEach(a => a.classList.remove('active'));
    
    // Close mobile menu
    document.getElementById('nav').classList.remove('open');
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Update URL hash
    history.pushState(null, '', '#' + page);
}

// ===== Language Toggle =====
function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'ar' : 'en';
    applyLanguage();
}

function applyLanguage() {
    const langBtn = document.getElementById('langBtn');
    const body = document.body;
    const html = document.documentElement;
    
    if (currentLang === 'ar') {
        body.setAttribute('dir', 'rtl');
        html.setAttribute('dir', 'rtl');
        html.setAttribute('lang', 'ar');
        langBtn.textContent = 'English';
    } else {
        body.setAttribute('dir', 'ltr');
        html.setAttribute('dir', 'ltr');
        html.setAttribute('lang', 'en');
        langBtn.textContent = 'العربية';
    }
    
    // Update all translatable elements
    document.querySelectorAll('[data-en]').forEach(el => {
        const text = el.getAttribute('data-' + currentLang);
        if (text) {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = text;
            } else {
                el.textContent = text;
            }
        }
    });
}

// ===== Mobile Menu =====
function toggleMenu() {
    const nav = document.getElementById('nav');
    nav.classList.toggle('open');
}

// ===== Header Scroll Hide =====
let lastScrollY = 0;
let ticking = false;

function handleScroll() {
    const header = document.getElementById('header');
    const currentScrollY = window.scrollY;
    
    if (currentScrollY > lastScrollY && currentScrollY > 100) {
        header.classList.add('hidden');
    } else {
        header.classList.remove('hidden');
    }
    
    lastScrollY = currentScrollY;
    ticking = false;
}

window.addEventListener('scroll', () => {
    if (!ticking) {
        window.requestAnimationFrame(handleScroll);
        ticking = true;
    }
});

// ===== Handle URL Hash =====
function handleHash() {
    const hash = window.location.hash.replace('#', '');
    if (hash) {
        navigateTo(hash);
    }
}

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    handleHash();
    
    // Close menu on outside click
    document.addEventListener('click', (e) => {
        const nav = document.getElementById('nav');
        const menuBtn = document.getElementById('menuBtn');
        if (!nav.contains(e.target) && !menuBtn.contains(e.target)) {
            nav.classList.remove('open');
        }
    });
});

// Handle browser back/forward
window.addEventListener('popstate', handleHash);
