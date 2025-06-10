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
