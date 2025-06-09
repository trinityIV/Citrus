/**
 * Citrus Music - Application principale
 * Architecture modulaire pour une meilleure maintenabilité
 */

// Importer les modules
import ParticlesEffect from './effects/particles.js';
import { initUI } from './modules/ui.js';
import { initPlayer } from './modules/player.js';
import { initDownloader } from './modules/downloader.js';
import { initLibrary } from './modules/library.js';
import { showNotification } from './modules/notifications.js';
import { SearchService } from './modules/search.js';
import { PlaylistService } from './modules/playlist.js';
import { initBatchDownloader } from './modules/batch.js';
import { initPreviews } from './modules/preview.js';

// Configuration globale
const CONFIG = {
    apiEndpoints: {
        download: '/api/download',
        search: '/api/search',
        playlist: '/api/playlist',
        library: '/api/library',
        status: '/api/status',
        stats: '/api/stats'
    },
    download: {
        maxConcurrent: 3,
        retryAttempts: 3,
        retryDelay: 1000
    },
    preview: {
        defaultVolume: 0.5,
        fadeInDuration: 200,
        fadeOutDuration: 200
    }
};

// Initialisation de l'application
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Initialiser les effets visuels
        new ParticlesEffect();
        
        // Initialiser l'interface utilisateur
        initUI();
        
        // Initialiser les services
        new SearchService(CONFIG);
        new PlaylistService(CONFIG);
        
        // Initialiser les modules audio
        initPlayer(CONFIG);
        initPreviews();
        
        // Initialiser les gestionnaires de téléchargement
        initDownloader(CONFIG);
        initBatchDownloader(CONFIG);
        
        // Initialiser la bibliothèque
        initLibrary(CONFIG);
        
        // Exposer certaines fonctions au contexte global
        window.showNotification = showNotification;
        
        console.log('Citrus Music App initialized successfully!');
        
    } catch (error) {
        console.error('Failed to initialize Citrus Music App:', error);
        showNotification(
            'Une erreur est survenue lors du démarrage de l\'application',
            'error'
        );
    }
});
