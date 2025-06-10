/**
 * Classe ParticlesEffect - Gère les effets de particules dans l'interface
 */
export default class ParticlesEffect {
  constructor() {
    this.init();
  }
  
  init() {
    // Initialiser les particules si l'élément canvas existe
    const canvas = document.getElementById('particles-js');
    if (canvas && window.particlesJS) {
      window.particlesJS('particles-js', this.getConfig());
    } else {
      // Créer le canvas s'il n'existe pas
      document.addEventListener('DOMContentLoaded', () => {
        const container = document.querySelector('.video-background');
        if (container) {
          const canvas = document.createElement('div');
          canvas.id = 'particles-js';
          container.appendChild(canvas);
          
          if (typeof particlesJS !== 'undefined') {
            window.particlesJS('particles-js', this.getConfig());
          }
        }
      });
    }
  }
  
  getConfig() {
    return {
      // Configuration des particules
      particles: {
        number: {
          value: 50,
          density: {
            enable: true,
            value_area: 800
          }
        },
        color: {
          value: "#ffffff"
        },
        shape: {
          type: "circle"
        },
        opacity: {
          value: 0.5,
          random: true
        },
        size: {
          value: 3,
          random: true
        },
        line_linked: {
          enable: true,
          distance: 150,
          color: "#ffffff",
          opacity: 0.4,
          width: 1
        },
        move: {
          enable: true,
          speed: 2,
          direction: "none",
          random: true,
          straight: false,
          out_mode: "out",
          bounce: false
        }
      },
      interactivity: {
        detect_on: "canvas",
        events: {
          onhover: {
            enable: true,
            mode: "grab"
          },
          onclick: {
            enable: true,
            mode: "push"
          },
          resize: true
        },
        modes: {
          grab: {
            distance: 140,
            line_linked: {
              opacity: 1
            }
          },
          push: {
            particles_nb: 4
          }
        }
      },
      retina_detect: true
    };
  }
}
