/**
 * Module UI - Gestion de l'interface utilisateur
 */

// Initialisation de l'interface utilisateur
export function initUI() {
    initMobileMenu();
    initTabs();
    initParticles();
    initThemeToggle();
}

// Gestion du menu mobile
function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');
    
    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
        
        // Fermer le menu lors du clic à l'extérieur
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        });
        
        // Fermer le menu mobile lors du clic sur un lien
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                sidebar.classList.remove('active');
            });
        });
    }
}

// Gestion des onglets
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');
            const selectedContent = document.getElementById(`${tabId}Tab`);
            
            if (!selectedContent || tab.classList.contains('active')) return;
            
            // Retirer la classe active de tous les onglets
            tabs.forEach(t => t.classList.remove('active'));
            
            // Ajouter la classe active à l'onglet cliqué
            tab.classList.add('active');
            
            // Masquer tous les contenus d'onglets avec animation
            tabContents.forEach(content => {
                if (content.classList.contains('active')) {
                    content.classList.add('fade-out');
                    setTimeout(() => {
                        content.classList.remove('active', 'fade-out');
                    }, 300);
                }
            });
            
            // Afficher le nouveau contenu avec animation
            setTimeout(() => {
                selectedContent.classList.add('active');
            }, 300);
        });
    });
    
    // Activer le premier onglet par défaut
    const defaultTab = tabs[0];
    if (defaultTab) {
        defaultTab.click();
    }
}

// Effet de particules
function initParticles() {
    const particlesContainer = document.getElementById('particles');
    
    if (!particlesContainer) return;
    
    // Créer des particules
    for (let i = 0; i < 30; i++) {
        createParticle(particlesContainer);
    }
}

// Créer une particule
function createParticle(container) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    
    // Taille aléatoire
    const size = Math.random() * 5 + 2;
    particle.style.width = `${size}px`;
    particle.style.height = `${size}px`;
    
    // Position aléatoire
    particle.style.left = `${Math.random() * 100}%`;
    particle.style.top = `${Math.random() * 100}%`;
    
    // Délai d'animation aléatoire
    particle.style.animationDelay = `${Math.random() * 15}s`;
    
    // Durée d'animation aléatoire
    particle.style.animationDuration = `${Math.random() * 15 + 10}s`;
    
    // Ajouter au conteneur
    container.appendChild(particle);
    
    // Recréer la particule après la fin de l'animation
    particle.addEventListener('animationend', () => {
        particle.remove();
        createParticle(container);
    });
}

// Basculement du thème (clair/sombre)
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    
    if (themeToggle) {
        // Vérifier le thème actuel
        const currentTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', currentTheme);
        
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
}
