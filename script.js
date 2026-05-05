// ===== AGRIYOUTH WEBSITE SCRIPTS =====

document.addEventListener('DOMContentLoaded', function() {
    // State
    let currentLang = 'en';

    // Elements
    const html = document.documentElement;
    const langSwitcher = document.getElementById('langSwitcher');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mainNav = document.getElementById('mainNav');
    const header = document.getElementById('siteHeader');
    const navLinks = document.querySelectorAll('.nav-link');

    // ===== LANGUAGE SWITCHER =====
    function switchLanguage(lang) {
        currentLang = lang;
        
        if (lang === 'ar') {
            html.setAttribute('dir', 'rtl');
            html.setAttribute('lang', 'ar');
        } else {
            html.setAttribute('dir', 'ltr');
            html.setAttribute('lang', 'en');
        }

        // Update all elements with data-en/data-ar attributes
        const elements = document.querySelectorAll('[data-en][data-ar]');
        elements.forEach(el => {
            const text = el.getAttribute('data-' + lang);
            if (text) {
                el.textContent = text;
            }
        });

        // Update lang switcher button text
        langSwitcher.textContent = lang === 'en' ? 'العربية' : 'English';

        // Store preference
        localStorage.setItem('agriyouth-lang', lang);
    }

    langSwitcher.addEventListener('click', function() {
        const newLang = currentLang === 'en' ? 'ar' : 'en';
        switchLanguage(newLang);
    });

    // Check stored language preference
    const storedLang = localStorage.getItem('agriyouth-lang');
    if (storedLang) {
        switchLanguage(storedLang);
    }

    // ===== MOBILE MENU =====
    mobileMenuBtn.addEventListener('click', function() {
        mainNav.classList.toggle('active');
        this.classList.toggle('active');
    });

    // Close mobile menu on link click
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            mainNav.classList.remove('active');
            mobileMenuBtn.classList.remove('active');
        });
    });

    // ===== STICKY HEADER =====
    let lastScroll = 0;
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }

        lastScroll = currentScroll;
    });

    // ===== ACTIVE NAV LINK =====
    function updateActiveNav() {
        const sections = document.querySelectorAll('section[id]');
        const scrollPos = window.scrollY + 100;

        sections.forEach(section => {
            const top = section.offsetTop;
            const height = section.offsetHeight;
            const id = section.getAttribute('id');

            if (scrollPos >= top && scrollPos < top + height) {
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === '#' + id) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }

    window.addEventListener('scroll', updateActiveNav);

    // ===== INTERSECTION OBSERVER FOR ANIMATIONS =====
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe cards and items
    const animateElements = document.querySelectorAll(
        '.initiative-card, .category-card, .level-card, .pillar-card, .goal-item, .why-item, .objective-item, .contact-card, .stat-item'
    );
    animateElements.forEach(el => {
        el.style.opacity = '0';
        observer.observe(el);
    });

    // ===== SMOOTH SCROLL FOR ANCHOR LINKS =====
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});
