/**
 * Module SearchService - Gestion de la recherche musicale
 */

import { showNotification } from './notifications.js';
import { preview } from './preview.js';

export class SearchService {
    constructor(config) {
        this.config = config;
        this.searchInput = document.getElementById('searchInput');
        this.searchResults = document.getElementById('searchResults');
        this.searchTimeout = null;
        this.cache = new Map();
        
        // Initialiser la recherche
        this.init();
    }
    
    /**
     * Initialise le service de recherche
     */
    init() {
        if (!this.searchInput || !this.searchResults) return;
        
        // Événement de saisie avec debounce
        this.searchInput.addEventListener('input', () => {
            clearTimeout(this.searchTimeout);
            
            const query = this.searchInput.value.trim();
            if (query.length < 2) {
                this.clearResults();
                return;
            }
            
            this.searchTimeout = setTimeout(() => {
                this.search(query);
            }, 500);
        });
        
        // Événement de nettoyage au changement d'onglet
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                if (!tab.dataset.tab.includes('search')) {
                    preview.stopPreview();
                }
            });
        });
    }
    
    /**
     * Effectue une recherche
     */
    async search(query) {
        try {
            // Vérifier le cache
            if (this.cache.has(query)) {
                this.displayResults(this.cache.get(query));
                return;
            }
            
            // Afficher le chargement
            this.searchResults.innerHTML = '<div class="loading">Recherche en cours...</div>';
            
            // Faire la requête à l'API
            const response = await fetch(`${this.config.apiEndpoints.search}?q=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error('Erreur réseau');
            
            const results = await response.json();
            
            // Mettre en cache
            this.cache.set(query, results);
            
            // Afficher les résultats
            this.displayResults(results);
            
        } catch (error) {
            console.error('Erreur de recherche:', error);
            showNotification('Erreur lors de la recherche', 'error');
            this.searchResults.innerHTML = '<div class="error">Une erreur est survenue</div>';
        }
    }
    
    /**
     * Affiche les résultats de recherche
     */
    displayResults(results) {
        if (!results || results.length === 0) {
            this.searchResults.innerHTML = '<div class="no-results">Aucun résultat trouvé</div>';
            return;
        }
        
        const html = results.map(track => `
            <div class="search-result" data-id="${track.id}">
                <div class="result-thumbnail">
                    <img src="${track.thumbnail || '/static/img/default-cover.png'}" alt="${track.title}">
                </div>
                <div class="result-info">
                    <h3>${track.title}</h3>
                    <p>${track.artist}</p>
                    <span class="result-duration">${this.formatDuration(track.duration)}</span>
                    <span class="result-source">${track.source}</span>
                </div>
                <div class="result-actions">
                    ${track.previewUrl ? `
                        <button class="btn-preview" data-preview-id="${track.id}" data-track='${JSON.stringify(track)}'>
                            <i class="fas fa-play"></i>
                        </button>
                    ` : ''}
                    <button class="btn-download" data-track='${JSON.stringify(track)}'>
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        this.searchResults.innerHTML = html;
        
        // Ajouter les événements de téléchargement
        this.searchResults.querySelectorAll('.btn-download').forEach(button => {
            button.addEventListener('click', () => {
                const trackData = JSON.parse(button.dataset.track);
                this.downloadTrack(trackData);
            });
        });
    }
    
    /**
     * Lance le téléchargement d'une piste
     */
    async downloadTrack(track) {
        try {
            const response = await fetch(this.config.apiEndpoints.download, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(track)
            });
            
            if (!response.ok) throw new Error('Erreur réseau');
            
            const data = await response.json();
            showNotification(
                `Téléchargement démarré: ${track.title}`,
                'success'
            );
            
        } catch (error) {
            console.error('Erreur de téléchargement:', error);
            showNotification(
                `Erreur lors du téléchargement de ${track.title}`,
                'error'
            );
        }
    }
    
    /**
     * Efface les résultats de recherche
     */
    clearResults() {
        if (this.searchResults) {
            this.searchResults.innerHTML = '';
        }
        preview.stopPreview();
    }
    
    /**
     * Formate la durée en MM:SS
     */
    formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
    }
}


