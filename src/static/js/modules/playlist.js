/**
 * Module Playlist - Gestion des playlists (scrapping only, yt-dlp)
 * Aucun token ou clé API nécessaire.
 */

import { showNotification } from './notifications.js';
import { preview } from './preview.js';

export class PlaylistService {
    constructor(config) {
        this.config = config;
        this.playlistInput = document.getElementById('playlistInput');
        this.playlistContainer = document.getElementById('playlistContainer');
        this.currentPlaylist = null;
        
        this.init();
    }
    
    /**
     * Initialise le service de playlist
     */
    init() {
        if (!this.playlistInput || !this.playlistContainer) return;
        
        // Écouter les changements d'URL de playlist
        this.playlistInput.addEventListener('change', (e) => {
            const url = e.target.value.trim();
            if (url) {
                this.loadPlaylist(url);
            }
        });
        
        // Écouter les événements de nettoyage au changement d'onglet
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                if (!tab.dataset.tab.includes('playlist')) {
                    preview.stopPreview();
                }
            });
        });
    }
    
    /**
     * Charge les informations d'une playlist
     */
    async loadPlaylist(url) {
        try {
            this.showLoading();
            
            const response = await fetch(this.config.apiEndpoints.playlist, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            });
            
            if (!response.ok) throw new Error('Erreur réseau ou scrapping');
            
            const playlist = await response.json();
            this.currentPlaylist = playlist;
            this.displayPlaylist(playlist);
            
        } catch (error) {
            console.error('Erreur playlist:', error);
            showNotification(
                'Impossible de charger la playlist. Vérifiez l\'URL.',
                'error'
            );
            this.showError();
        } finally {
            this.hideLoading();
        }
    }
    
    /**
     * Affiche une playlist
     */
    displayPlaylist(playlist) {
        if (!playlist || !playlist.tracks) return;
        
        const html = `
            <div class="playlist-header">
                <div class="playlist-info">
                    <div class="playlist-thumbnail">
                        <img src="${playlist.thumbnail || '/static/img/default-cover.png'}" 
                             alt="${playlist.title}">
                    </div>
                    <div class="playlist-details">
                        <h3>${playlist.title}</h3>
                        ${playlist.description ? `<p>${playlist.description}</p>` : ''}
                        <span class="playlist-count">${playlist.tracks.length} titres</span>
                    </div>
                </div>
                <div class="playlist-actions">
                    <button class="btn-download-all" data-playlist='${JSON.stringify(playlist)}'>
                        <i class="fas fa-download"></i>
                        Tout télécharger
                    </button>
                </div>
            </div>
            
            <div class="playlist-tracks">
                ${playlist.tracks.map((track, index) => `
                    <div class="track-item" data-track-id="${track.id}">
                        <div class="track-number">${index + 1}</div>
                        <div class="track-info">
                            <h4>${track.title}</h4>
                            <p>${track.artist}</p>
                        </div>
                        <div class="track-meta">
                            <span class="track-duration">${this.formatDuration(track.duration)}</span>
                            <span class="track-source">${track.source}</span>
                        </div>
                        <div class="track-actions">
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
                `).join('')}
            </div>
            
            <div id="batchProgress"></div>
        `;
        
        this.playlistContainer.innerHTML = html;
        
        // Ajouter les événements
        const downloadAllBtn = this.playlistContainer.querySelector('.btn-download-all');
        if (downloadAllBtn) {
            downloadAllBtn.addEventListener('click', () => {
                const playlistData = JSON.parse(downloadAllBtn.dataset.playlist);
                document.dispatchEvent(new CustomEvent('downloadPlaylist', {
                    detail: playlistData
                }));
            });
        }
        
        // Événements de téléchargement individuel
        this.playlistContainer.querySelectorAll('.btn-download').forEach(button => {
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
     * Formate la durée en MM:SS
     */
    formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
    }
    
    /**
     * Affiche le chargement
     */
    showLoading() {
        if (this.playlistContainer) {
            this.playlistContainer.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Chargement de la playlist...</p>
                </div>
            `;
        }
    }
    
    /**
     * Cache le chargement
     */
    hideLoading() {
        const loading = this.playlistContainer?.querySelector('.loading');
        if (loading) {
            loading.remove();
        }
    }
    
    /**
     * Affiche une erreur
     */
    showError() {
        if (this.playlistContainer) {
            this.playlistContainer.innerHTML = `
                <div class="error">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Impossible de charger la playlist</p>
                </div>
            `;
        }
    }
}

// Export une instance unique du service de playlist
export const playlistService = new PlaylistService();

