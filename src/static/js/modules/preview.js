/**
 * Module Preview - Gestion de la prévisualisation audio
 */

import { showNotification } from './notifications.js';

class PreviewPlayer {
    constructor() {
        this.audio = new Audio();
        this.currentPreview = null;
        this.isPlaying = false;
        this.volume = localStorage.getItem('previewVolume') || 0.5;
        
        // Configurer le volume initial
        this.audio.volume = this.volume;
        
        // Événements audio
        this.audio.addEventListener('ended', () => {
            this.stopPreview();
        });
        
        this.audio.addEventListener('error', (e) => {
            console.error('Erreur de prévisualisation:', e);
            showNotification('Impossible de charger la prévisualisation', 'error');
            this.stopPreview();
        });
    }
    
    /**
     * Démarre la prévisualisation d'une piste
     */
    startPreview(track) {
        // Si une prévisualisation est en cours, l'arrêter
        if (this.isPlaying) {
            this.stopPreview();
        }
        
        // Vérifier si la piste a une URL de prévisualisation
        if (!track.previewUrl) {
            showNotification('Pas de prévisualisation disponible', 'info');
            return;
        }
        
        // Mettre à jour l'élément audio
        this.audio.src = track.previewUrl;
        this.currentPreview = track;
        
        // Lancer la lecture
        this.audio.play().then(() => {
            this.isPlaying = true;
            
            // Mettre à jour l'interface
            this.updatePreviewUI(track, true);
            
            // Afficher une notification
            showNotification(
                `Prévisualisation: ${track.title} - ${track.artist}`,
                'info'
            );
        }).catch(error => {
            console.error('Erreur de lecture:', error);
            showNotification('Impossible de lire la prévisualisation', 'error');
        });
    }
    
    /**
     * Arrête la prévisualisation en cours
     */
    stopPreview() {
        if (!this.isPlaying) return;
        
        this.audio.pause();
        this.audio.currentTime = 0;
        this.isPlaying = false;
        
        // Mettre à jour l'interface
        if (this.currentPreview) {
            this.updatePreviewUI(this.currentPreview, false);
        }
        
        this.currentPreview = null;
    }
    
    /**
     * Met à jour l'interface pour la prévisualisation
     */
    updatePreviewUI(track, isPlaying) {
        // Trouver tous les boutons de prévisualisation pour cette piste
        const previewButtons = document.querySelectorAll(
            `[data-preview-id="${track.id}"]`
        );
        
        previewButtons.forEach(button => {
            const icon = button.querySelector('i');
            if (icon) {
                icon.className = isPlaying ? 'fas fa-stop' : 'fas fa-play';
            }
            button.classList.toggle('playing', isPlaying);
        });
    }
    
    /**
     * Change le volume de prévisualisation
     */
    setVolume(volume) {
        this.volume = volume;
        this.audio.volume = volume;
        localStorage.setItem('previewVolume', volume);
    }
}

// Instance unique du lecteur de prévisualisation
const previewPlayer = new PreviewPlayer();

/**
 * Initialise les boutons de prévisualisation
 */
export function initPreviews() {
    // Ajouter les événements aux boutons de prévisualisation
    document.addEventListener('click', (e) => {
        const previewButton = e.target.closest('[data-preview-id]');
        if (!previewButton) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        const trackId = previewButton.dataset.previewId;
        const trackData = JSON.parse(previewButton.dataset.track);
        
        // Si c'est la piste en cours, arrêter la prévisualisation
        if (
            previewPlayer.isPlaying && 
            previewPlayer.currentPreview && 
            previewPlayer.currentPreview.id === trackId
        ) {
            previewPlayer.stopPreview();
        } else {
            previewPlayer.startPreview(trackData);
        }
    });
    
    // Ajouter le contrôle du volume si présent
    const volumeControl = document.getElementById('previewVolume');
    if (volumeControl) {
        volumeControl.value = previewPlayer.volume;
        volumeControl.addEventListener('input', (e) => {
            previewPlayer.setVolume(e.target.value);
        });
    }
}

// Exposer le lecteur de prévisualisation
export const preview = previewPlayer;
