/**
 * Welcome page JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add scroll effect to header
    const header = document.querySelector('.header');
    let lastScrollTop = 0;
    
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > 100) {
            header.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        } else {
            header.style.boxShadow = 'none';
        }
        
        lastScrollTop = scrollTop;
    });

    // Animate feature cards on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe feature cards and version cards
    const animatedElements = document.querySelectorAll('.feature-card, .version-card, .guide-card');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

    // Copy command functionality for CLI installation
    const copyButtons = document.querySelectorAll('.btn-primary');
    copyButtons.forEach(button => {
        if (button.textContent.includes('pip install')) {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Copy to clipboard
                const command = 'pip install gopnik';
                navigator.clipboard.writeText(command).then(() => {
                    const originalText = button.textContent;
                    button.textContent = 'Copied!';
                    button.style.background = '#10b981';
                    
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.style.background = '#3b82f6';
                    }, 2000);
                }).catch(() => {
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = command;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    
                    const originalText = button.textContent;
                    button.textContent = 'Copied!';
                    button.style.background = '#10b981';
                    
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.style.background = '#3b82f6';
                    }, 2000);
                });
            });
        }
    });

    // Demo preview animation
    const demoPreview = document.querySelector('.demo-preview');
    if (demoPreview) {
        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Animate the redaction process
                    setTimeout(() => {
                        const piiElements = document.querySelectorAll('.pii');
                        piiElements.forEach((el, index) => {
                            setTimeout(() => {
                                el.style.transition = 'all 0.5s ease';
                                el.style.background = '#374151';
                                el.style.color = '#374151';
                            }, index * 200);
                        });
                    }, 1000);
                }
            });
        }, { threshold: 0.5 });
        
        observer.observe(demoPreview);
    }

    // Add loading states for external links
    const externalLinks = document.querySelectorAll('a[href^="http"], a[href^="#"]');
    externalLinks.forEach(link => {
        if (!link.href.includes(window.location.hostname) && link.href.startsWith('http')) {
            link.addEventListener('click', function() {
                this.style.opacity = '0.7';
                this.textContent += ' ↗';
            });
        }
    });

    // Mobile menu toggle (basic implementation)
    const createMobileMenu = () => {
        const nav = document.querySelector('.nav');
        const header = document.querySelector('.header .container');
        
        if (window.innerWidth <= 768) {
            if (!document.querySelector('.mobile-menu-toggle')) {
                const toggle = document.createElement('button');
                toggle.className = 'mobile-menu-toggle';
                toggle.innerHTML = '☰';
                toggle.style.cssText = `
                    background: none;
                    border: none;
                    font-size: 1.5rem;
                    cursor: pointer;
                    color: #1f2937;
                `;
                
                toggle.addEventListener('click', () => {
                    nav.style.display = nav.style.display === 'flex' ? 'none' : 'flex';
                    nav.style.position = 'absolute';
                    nav.style.top = '100%';
                    nav.style.left = '0';
                    nav.style.right = '0';
                    nav.style.background = 'white';
                    nav.style.flexDirection = 'column';
                    nav.style.padding = '1rem';
                    nav.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
                });
                
                header.appendChild(toggle);
            }
        }
    };

    // Initialize mobile menu
    createMobileMenu();
    window.addEventListener('resize', createMobileMenu);
});