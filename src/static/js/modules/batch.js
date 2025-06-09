/**
 * Module Batch - Gestion des téléchargements en masse
 */

import { showNotification } from './notifications.js';

class BatchDownloader {
    constructor(config) {
        this.config = config;
        this.queue = [];
        this.isProcessing = false;
        this.currentDownload = null;
        this.maxConcurrent = 3;
        this.activeDownloads = 0;
        
        // Initialiser l'interface
        this.init();
    }
    
    /**
     * Initialise le gestionnaire de téléchargements en masse
     */
    init() {
        // Écouter les événements de téléchargement de playlist
        document.addEventListener('downloadPlaylist', (e) => {
            const playlist = e.detail;
            this.addPlaylistToQueue(playlist);
        });
        
        // Écouter les événements d'annulation
        document.addEventListener('cancelBatchDownload', () => {
            this.cancelCurrentDownload();
        });
    }
    
    /**
     * Ajoute une playlist à la file d'attente
     */
    addPlaylistToQueue(playlist) {
        // Vérifier si la playlist est valide
        if (!playlist || !playlist.tracks || playlist.tracks.length === 0) {
            showNotification('Playlist invalide', 'error');
            return;
        }
        
        // Ajouter chaque piste à la file
        playlist.tracks.forEach(track => {
            this.queue.push({
                track,
                playlist: {
                    id: playlist.id,
                    title: playlist.title
                },
                status: 'pending'
            });
        });
        
        showNotification(
            `${playlist.tracks.length} pistes ajoutées à la file d'attente`,
            'info'
        );
        
        // Démarrer le traitement si ce n'est pas déjà fait
        if (!this.isProcessing) {
            this.processQueue();
        }
        
        // Mettre à jour l'interface
        this.updateUI();
    }
    
    /**
     * Traite la file d'attente
     */
    async processQueue() {
        if (this.isProcessing || this.queue.length === 0) return;
        
        this.isProcessing = true;
        
        while (this.queue.length > 0 && this.activeDownloads < this.maxConcurrent) {
            const item = this.queue.find(i => i.status === 'pending');
            if (!item) break;
            
            item.status = 'downloading';
            this.activeDownloads++;
            
            this.updateUI();
            
            try {
                await this.downloadTrack(item);
                item.status = 'completed';
                showNotification(
                    `${item.track.title} téléchargé avec succès`,
                    'success'
                );
            } catch (error) {
                item.status = 'error';
                item.error = error.message;
                showNotification(
                    `Erreur lors du téléchargement de ${item.track.title}`,
                    'error'
                );
            }
            
            this.activeDownloads--;
            this.updateUI();
        }
        
        // Vérifier s'il reste des téléchargements en attente
        if (this.queue.some(i => i.status === 'pending')) {
            setTimeout(() => this.processQueue(), 1000);
        } else {
            this.isProcessing = false;
            
            // Vérifier si tous les téléchargements sont terminés
            const failed = this.queue.filter(i => i.status === 'error').length;
            const total = this.queue.length;
            
            if (failed === 0) {
                showNotification(
                    `Tous les téléchargements sont terminés (${total} pistes)`,
                    'success'
                );
            } else {
                showNotification(
                    `Téléchargements terminés avec ${failed} erreurs sur ${total} pistes`,
                    'warning'
                );
            }
        }
    }
    
    /**
     * Télécharge une piste
     */
    async downloadTrack(item) {
        try {
            const response = await fetch(this.config.apiEndpoints.download, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...item.track,
                    playlist: item.playlist
                })
            });
            
            if (!response.ok) {
                throw new Error('Erreur réseau');
            }
            
            return await response.json();
            
        } catch (error) {
            console.error('Erreur de téléchargement:', error);
            throw error;
        }
    }
    
    /**
     * Annule le téléchargement en cours
     */
    cancelCurrentDownload() {
        // Marquer les téléchargements en cours comme annulés
        this.queue.forEach(item => {
            if (item.status === 'downloading') {
                item.status = 'cancelled';
            }
        });
        
        this.isProcessing = false;
        this.activeDownloads = 0;
        
        showNotification('Téléchargements annulés', 'info');
        this.updateUI();
    }
    
    /**
     * Met à jour l'interface utilisateur
     */
    updateUI() {
        const batchProgress = document.getElementById('batchProgress');
        if (!batchProgress) return;
        
        const total = this.queue.length;
        const completed = this.queue.filter(i => i.status === 'completed').length;
        const failed = this.queue.filter(i => i.status === 'error').length;
        const cancelled = this.queue.filter(i => i.status === 'cancelled').length;
        const active = this.queue.filter(i => i.status === 'downloading').length;
        const pending = this.queue.filter(i => i.status === 'pending').length;
        
        const progress = Math.round((completed / total) * 100);
        
        batchProgress.innerHTML = `
            <div class="batch-stats">
                <div class="stat">
                    <span class="label">Total</span>
                    <span class="value">${total}</span>
                </div>
                <div class="stat">
                    <span class="label">Terminés</span>
                    <span class="value success">${completed}</span>
                </div>
                <div class="stat">
                    <span class="label">En cours</span>
                    <span class="value info">${active}</span>
                </div>
                <div class="stat">
                    <span class="label">En attente</span>
                    <span class="value">${pending}</span>
                </div>
                <div class="stat">
                    <span class="label">Échoués</span>
                    <span class="value error">${failed}</span>
                </div>
                <div class="stat">
                    <span class="label">Annulés</span>
                    <span class="value warning">${cancelled}</span>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress" style="width: ${progress}%"></div>
            </div>
            ${active > 0 ? `
                <button class="btn-cancel" onclick="dispatchEvent(new Event('cancelBatchDownload'))">
                    <i class="fas fa-stop"></i> Annuler
                </button>
            ` : ''}
        `;
    }
}

// Créer et exporter l'instance
let batchDownloader;

export function initBatchDownloader(config) {
    if (!batchDownloader) {
        batchDownloader = new BatchDownloader(config);
    }
    return batchDownloader;
}
