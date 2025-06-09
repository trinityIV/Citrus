/**
 * Module Effects - Effets visuels et animations
 */

// Initialisation des effets visuels
export function initEffects() {
    initWaves();
    initParticles();
    initScrollEffects();
}

// Animation des vagues
function initWaves() {
    const wavesContainer = document.getElementById('waves');
    
    if (!wavesContainer) return;
    
    // Créer les vagues
    for (let i = 1; i <= 3; i++) {
        const wave = document.createElement('div');
        wave.className = `wave wave-${i}`;
        wavesContainer.appendChild(wave);
    }
    
    // Animation des vagues en fonction du défilement
    window.addEventListener('scroll', () => {
        const scrollY = window.scrollY;
        const height = window.innerHeight;
        const scrollPercent = scrollY / height;
        
        // Déplacer les vagues à des vitesses différentes
        const waves = wavesContainer.querySelectorAll('.wave');
        
        if (waves.length > 0) {
            waves[0].style.transform = `translate3d(0, ${scrollPercent * 15}px, 0)`;
            
            if (waves.length > 1) {
                waves[1].style.transform = `translate3d(0, ${scrollPercent * 25}px, 0)`;
                
                if (waves.length > 2) {
                    waves[2].style.transform = `translate3d(0, ${scrollPercent * 35}px, 0)`;
                }
            }
        }
    });
}

// Effet de particules
function initParticles() {
    const particlesContainer = document.getElementById('particles');
    
    if (!particlesContainer) return;
    
    // Nettoyer les particules existantes
    particlesContainer.innerHTML = '';
    
    // Créer des particules
    const particleCount = window.innerWidth < 768 ? 15 : 30;
    
    for (let i = 0; i < particleCount; i++) {
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
    
    // Opacité aléatoire
    particle.style.opacity = Math.random() * 0.5 + 0.2;
    
    // Ajouter au conteneur
    container.appendChild(particle);
    
    // Recréer la particule après la fin de l'animation
    particle.addEventListener('animationend', () => {
        particle.remove();
        createParticle(container);
    });
}

// Effets au défilement
function initScrollEffects() {
    // Animation des éléments au défilement
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.animate-on-scroll');
        
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementBottom = element.getBoundingClientRect().bottom;
            const windowHeight = window.innerHeight;
            
            // Si l'élément est visible dans la fenêtre
            if (elementTop < windowHeight - 100 && elementBottom > 0) {
                element.classList.add('animated');
            }
        });
    };
    
    // Exécuter une fois au chargement
    window.addEventListener('load', animateOnScroll);
    
    // Exécuter au défilement
    window.addEventListener('scroll', animateOnScroll);
    
    // Animation du fond au défilement
    window.addEventListener('scroll', () => {
        const scrollY = window.scrollY;
        const body = document.body;
        
        // Ajuster la luminosité du fond en fonction du défilement
        const brightness = 100 - Math.min(scrollY / 10, 15);
        body.style.setProperty('--background-brightness', `${brightness}%`);
        
        // Effet parallaxe pour le héros
        const hero = document.querySelector('.hero');
        if (hero) {
            const translateY = scrollY * 0.3;
            hero.style.transform = `translateY(${translateY}px)`;
            hero.style.opacity = 1 - (scrollY / 500);
        }
    });
}

// Effet de hover sur les cartes
export function initCardHoverEffects() {
    const cards = document.querySelectorAll('.track-card, .playlist-card');
    
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const angleX = (y - centerY) / 20;
            const angleY = (centerX - x) / 20;
            
            card.style.transform = `perspective(1000px) rotateX(${angleX}deg) rotateY(${angleY}deg) scale3d(1.02, 1.02, 1.02)`;
            card.style.boxShadow = `0 15px 35px rgba(0, 0, 0, 0.2), ${(x - centerX) / 25}px ${(y - centerY) / 25}px 30px rgba(0, 0, 0, 0.1)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
            card.style.boxShadow = '';
        });
    });
}

// Effet de glassmorphisme dynamique
export function initGlassmorphism() {
    const glassElements = document.querySelectorAll('.glass');
    
    // Mettre à jour l'effet en fonction de la position de la souris
    document.addEventListener('mousemove', (e) => {
        const mouseX = e.clientX;
        const mouseY = e.clientY;
        
        glassElements.forEach(element => {
            const rect = element.getBoundingClientRect();
            const elementCenterX = rect.left + rect.width / 2;
            const elementCenterY = rect.top + rect.height / 2;
            
            const distanceX = mouseX - elementCenterX;
            const distanceY = mouseY - elementCenterY;
            const distance = Math.sqrt(distanceX * distanceX + distanceY * distanceY);
            
            // Ajuster l'opacité et le flou en fonction de la distance
            const maxDistance = 500;
            const opacity = 0.15 + Math.min(0.1, (maxDistance - Math.min(distance, maxDistance)) / maxDistance * 0.1);
            const blur = 10 + Math.min(5, (maxDistance - Math.min(distance, maxDistance)) / maxDistance * 5);
            
            element.style.backgroundColor = `rgba(255, 255, 255, ${opacity})`;
            element.style.backdropFilter = `blur(${blur}px)`;
        });
    });
}

// Effet de néon sur les éléments
export function initNeonEffect() {
    const neonElements = document.querySelectorAll('.neon');
    
    neonElements.forEach(element => {
        // Couleur de base
        const color = element.getAttribute('data-neon-color') || '#ff9d00';
        
        // Appliquer l'effet néon
        element.style.textShadow = `0 0 5px ${color}, 0 0 10px ${color}, 0 0 20px ${color}, 0 0 40px ${color}`;
        
        // Animation de pulsation
        element.style.animation = 'neon-pulse 2s infinite alternate';
    });
}

// Exporter toutes les fonctions d'effets
export { initWaves, initParticles, initScrollEffects };
