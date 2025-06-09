/**
 * Module Notifications - Système de notifications
 */

// Afficher une notification
export function showNotification(message, type = 'info') {
    // Créer l'élément de notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Ajouter l'icône en fonction du type
    let icon = 'fa-info-circle';
    
    switch (type) {
        case 'success':
            icon = 'fa-check-circle';
            break;
        case 'error':
            icon = 'fa-exclamation-circle';
            break;
        case 'warning':
            icon = 'fa-exclamation-triangle';
            break;
    }
    
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas ${icon}"></i>
        </div>
        <div class="notification-content">
            ${message}
        </div>
        <div class="notification-close">
            <i class="fas fa-times"></i>
        </div>
    `;
    
    // Ajouter la notification au corps du document
    document.body.appendChild(notification);
    
    // Afficher la notification avec une animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Ajouter un écouteur d'événements pour fermer la notification
    const closeBtn = notification.querySelector('.notification-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            closeNotification(notification);
        });
    }
    
    // Fermer automatiquement la notification après 5 secondes
    setTimeout(() => {
        closeNotification(notification);
    }, 5000);
}

// Fermer une notification
function closeNotification(notification) {
    notification.classList.add('fade-out');
    
    // Supprimer la notification après l'animation
    setTimeout(() => {
        notification.remove();
    }, 300);
}

// Ajouter les styles CSS pour les notifications
const notificationStyles = `
    .notification {
        position: fixed;
        bottom: 30px;
        right: 30px;
        padding: 15px;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        display: flex;
        align-items: center;
        min-width: 300px;
        max-width: 400px;
        transform: translateY(100px);
        opacity: 0;
        transition: transform 0.3s ease, opacity 0.3s ease;
        z-index: 1000;
        color: white;
    }
    
    .notification.show {
        transform: translateY(0);
        opacity: 1;
    }
    
    .notification.fade-out {
        transform: translateY(-20px);
        opacity: 0;
    }
    
    .notification-icon {
        margin-right: 15px;
        font-size: 20px;
        width: 24px;
        text-align: center;
    }
    
    .notification-content {
        flex: 1;
        font-weight: 500;
    }
    
    .notification-close {
        margin-left: 15px;
        cursor: pointer;
        opacity: 0.7;
        transition: opacity 0.2s;
    }
    
    .notification-close:hover {
        opacity: 1;
    }
    
    .notification.info {
        border-left: 4px solid #1E90FF;
    }
    
    .notification.info .notification-icon {
        color: #1E90FF;
    }
    
    .notification.success {
        border-left: 4px solid #32CD32;
    }
    
    .notification.success .notification-icon {
        color: #32CD32;
    }
    
    .notification.error {
        border-left: 4px solid #FF453A;
    }
    
    .notification.error .notification-icon {
        color: #FF453A;
    }
    
    .notification.warning {
        border-left: 4px solid #FFA500;
    }
    
    .notification.warning .notification-icon {
        color: #FFA500;
    }
    
    /* Ajuster la position pour les appareils mobiles */
    @media (max-width: 768px) {
        .notification {
            bottom: 20px;
            right: 20px;
            left: 20px;
            min-width: auto;
            max-width: none;
            width: calc(100% - 40px);
        }
    }
`;

// Ajouter les styles au chargement du document
document.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = notificationStyles;
    document.head.appendChild(style);
});
