// Module de gestion des téléchargements Citrus
// Gère les requêtes de téléchargement (YouTube, Spotify, etc.), le suivi de progression, l'affichage des statuts et le bypass frontend.

// Importer les utilitaires DOM pour une gestion sécurisée des éléments
import { getElement, getElementValue, setElementText, setElementVisibility } from '/static/js/dom-utils.js';
import { showNotification } from './notifications.js';

/**
 * Initialise le gestionnaire de téléchargements
 * @param {Object} config - Configuration globale de l'application
 */
export function initDownloader(config) {
    const downloadForm = getElement('downloadForm');
    
    // Vérifier si le formulaire existe avant d'ajouter des événements
    if (!downloadForm) {
        console.log('Formulaire de téléchargement non trouvé, module non initialisé');
        return;
    }
    
    downloadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Récupérer les valeurs des champs de manière sécurisée
        const url = getElementValue('downloadUrl');
        const service = getElementValue('downloadService', 'youtube');
        
        if (!url) {
            showNotification('Veuillez entrer une URL valide', 'error');
            return;
        }
        
        try {
            // Afficher le statut de téléchargement
            setElementText('downloadStatus', 'Téléchargement en cours...');
            setElementVisibility('downloadStatus', true);
            
            const result = await startDownload(url, service);
            
            // Afficher le résultat
            setElementText('downloadStatus', 'Téléchargement terminé!');
            setTimeout(() => {
                setElementVisibility('downloadStatus', false);
            }, 3000);
            
            showNotification('Téléchargement terminé avec succès!', 'success');
            
            // Réinitialiser le formulaire
            downloadForm.reset();
            
        } catch (error) {
            console.error('Erreur de téléchargement:', error);
            
            setElementText('downloadStatus', `Erreur: ${error.message}`);
            setTimeout(() => {
                setElementVisibility('downloadStatus', false);
            }, 5000);
            
            showNotification(`Erreur de téléchargement: ${error.message}`, 'error');
        }
    });
}

export async function startDownload(url, service) {
    const resp = await fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, service })
    });
    if (!resp.ok) throw new Error('Erreur lors de la requête de téléchargement');
    return await resp.json();
}

export async function getDownloadStatus(downloadId) {
    const resp = await fetch(`/api/download/status/${downloadId}`);
    if (!resp.ok) throw new Error('Erreur lors de la récupération du statut');
    return await resp.json();
}

// Fonction utilitaire pour bypass ou extraction spéciale si besoin (ex: cookies, headers, DRM)
export function drmBypasser(site, options = {}) {
    // Exemple de stratégie de contournement DRM (à adapter selon le backend)
    switch(site) {
        case 'youtube':
            // Youtube n'a pas de DRM fort, mais certains contenus sont chiffrés (ex: Widevine)
            // Ici, tu pourrais injecter des clefs, utiliser un proxy, ou appeler un backend spécialisé
            return { ...options, drm: 'widevine', injectKeys: true };
        case 'spotify':
            // Pour Spotify, spotDL contourne déjà le DRM côté backend
            return { ...options, drm: 'spotdl' };
        case 'netflix':
            // Pour Netflix, il faudrait un backend decrypter (hors scope légal)
            return { ...options, drm: 'widevine', needsBackend: true };
        default:
            return options;
    }
}

export function buildBypassOptions(site) {
    // Ajoute ici la logique de contournement spécifique (ex: YouTube age restriction, proxy, etc.)
    switch(site) {
        case 'youtube':
            return { headers: { 'X-Bypass': 'yt-age' }, ...drmBypasser('youtube') };
        // Ajoute d'autres cas si besoin
        default:
            return {};
    }
}

// TODO: Implement download logic for Citrus
