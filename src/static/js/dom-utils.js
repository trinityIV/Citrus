/**
 * Utilitaires DOM pour Citrus Music Server
 * Fournit des fonctions sécurisées pour manipuler le DOM
 */

/**
 * Récupère un élément DOM de manière sécurisée
 * @param {string} id - ID de l'élément à récupérer
 * @param {boolean} required - Si true, affiche un avertissement dans la console si l'élément n'est pas trouvé
 * @returns {HTMLElement|null} - L'élément DOM ou null s'il n'existe pas
 */
export function getElement(id, required = false) {
    const element = document.getElementById(id);
    if (!element && required) {
        console.warn(`Élément DOM avec ID "${id}" non trouvé mais requis`);
    }
    return element;
}

/**
 * Récupère la valeur d'un élément de formulaire de manière sécurisée
 * @param {string} id - ID de l'élément à récupérer
 * @param {string} defaultValue - Valeur par défaut si l'élément n'existe pas
 * @returns {string} - La valeur de l'élément ou la valeur par défaut
 */
export function getElementValue(id, defaultValue = '') {
    const element = getElement(id);
    return element && element.value ? element.value.trim() : defaultValue;
}

/**
 * Définit la valeur d'un élément de formulaire de manière sécurisée
 * @param {string} id - ID de l'élément à modifier
 * @param {string} value - Valeur à définir
 * @returns {boolean} - true si l'opération a réussi, false sinon
 */
export function setElementValue(id, value) {
    const element = getElement(id);
    if (element) {
        element.value = value;
        return true;
    }
    return false;
}

/**
 * Ajoute un gestionnaire d'événements à un élément de manière sécurisée
 * @param {string} id - ID de l'élément
 * @param {string} event - Nom de l'événement (ex: 'click', 'submit')
 * @param {Function} handler - Fonction de gestion de l'événement
 * @returns {boolean} - true si l'opération a réussi, false sinon
 */
export function addEventHandler(id, event, handler) {
    const element = getElement(id);
    if (element) {
        element.addEventListener(event, handler);
        return true;
    }
    return false;
}

/**
 * Affiche ou masque un élément de manière sécurisée
 * @param {string} id - ID de l'élément
 * @param {boolean} visible - true pour afficher, false pour masquer
 * @returns {boolean} - true si l'opération a réussi, false sinon
 */
export function setElementVisibility(id, visible) {
    const element = getElement(id);
    if (element) {
        element.style.display = visible ? 'block' : 'none';
        return true;
    }
    return false;
}

/**
 * Définit le contenu texte d'un élément de manière sécurisée
 * @param {string} id - ID de l'élément
 * @param {string} text - Texte à définir
 * @returns {boolean} - true si l'opération a réussi, false sinon
 */
export function setElementText(id, text) {
    const element = getElement(id);
    if (element) {
        element.textContent = text;
        return true;
    }
    return false;
}

/**
 * Crée un élément DOM avec des attributs et du contenu
 * @param {string} tag - Type d'élément à créer
 * @param {Object} attributes - Attributs à ajouter à l'élément
 * @param {string|HTMLElement|Array} content - Contenu à ajouter à l'élément
 * @returns {HTMLElement} - L'élément créé
 */
export function createElement(tag, attributes = {}, content = null) {
    const element = document.createElement(tag);
    
    // Ajouter les attributs
    Object.entries(attributes).forEach(([key, value]) => {
        if (key === 'className') {
            element.className = value;
        } else if (key === 'dataset') {
            Object.entries(value).forEach(([dataKey, dataValue]) => {
                element.dataset[dataKey] = dataValue;
            });
        } else {
            element.setAttribute(key, value);
        }
    });
    
    // Ajouter le contenu
    if (content) {
        if (Array.isArray(content)) {
            content.forEach(item => {
                if (item instanceof HTMLElement) {
                    element.appendChild(item);
                } else {
                    element.appendChild(document.createTextNode(item));
                }
            });
        } else if (content instanceof HTMLElement) {
            element.appendChild(content);
        } else {
            element.textContent = content;
        }
    }
    
    return element;
}

/**
 * Crée et affiche une modal
 * @param {string} id - ID de la modal
 * @param {string} title - Titre de la modal
 * @param {HTMLElement|string} content - Contenu de la modal
 * @param {Function} onClose - Fonction à exécuter à la fermeture
 * @returns {HTMLElement} - L'élément modal créé
 */
export function createModal(id, title, content, onClose = null) {
    // Supprimer la modal existante si elle existe
    const existingModal = getElement(id);
    if (existingModal) {
        existingModal.remove();
    }
    
    // Créer la structure de la modal
    const modalContent = createElement('div', { className: 'modal-content' }, [
        createElement('span', { className: 'close-modal', title: 'Fermer' }, '×'),
        createElement('h2', {}, title),
        typeof content === 'string' ? createElement('div', {}, content) : content
    ]);
    
    const modal = createElement('div', { id, className: 'modal' }, modalContent);
    document.body.appendChild(modal);
    
    // Gérer la fermeture
    const closeBtn = modal.querySelector('.close-modal');
    const closeModal = () => {
        modal.style.display = 'none';
        if (onClose && typeof onClose === 'function') {
            onClose();
        }
    };
    
    closeBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // Afficher la modal
    modal.style.display = 'flex';
    
    return modal;
}

/**
 * Ferme une modal par son ID
 * @param {string} id - ID de la modal à fermer
 */
export function closeModal(id) {
    const modal = getElement(id);
    if (modal) {
        modal.style.display = 'none';
    }
}
