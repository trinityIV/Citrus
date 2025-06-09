/**
 * Module Downloader - Gestion des téléchargements
 */

import { showNotification } from './notifications.js';
import { loadRecentTracks } from './library.js';

// Configuration globale
let config;

// Initialisation du gestionnaire de téléchargement
export function initDownloader(appConfig) {
    config = appConfig;
    initDownloadForm();
    loadActiveDownloads();
}

// Initialisation du formulaire de téléchargement
function initDownloadForm() {
    const downloadForm = document.getElementById('downloadForm');
    
    if (downloadForm) {
        downloadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const urlInput = downloadForm.querySelector('#downloadUrl');
            const serviceSelect = downloadForm.querySelector('#downloadService');
            const downloadBtn = downloadForm.querySelector('button[type="submit"]');
            
            const url = urlInput.value.trim();
            const service = serviceSelect.value;
            
            if (!url) {
                showNotification('Veuillez entrer une URL valide', 'error');
                return;
            }
            
            try {
                // Désactiver le bouton pendant le téléchargement
                downloadBtn.disabled = true;
                downloadBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Téléchargement...`;
                
                // Envoyer la requête au serveur
                const response = await fetch('/api/downloads', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        url: url,
                        service: service
                    })
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Erreur lors du téléchargement');
                }
                
                const data = await response.json();
                
                // Ajouter le téléchargement à la liste
                addDownloadItem(data.task_id, url, service);
                
                // Réinitialiser le formulaire
                urlInput.value = '';
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '<i class="fas fa-download"></i> Télécharger';
                
                // Afficher une notification
                showNotification('Téléchargement démarré', 'success');
            } catch (error) {
                console.error('Erreur:', error);
                showNotification(`Erreur: ${error.message}`, 'error');
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '<i class="fas fa-download"></i> Télécharger';
            }
        });
    }
}

// Charger les téléchargements actifs
async function loadActiveDownloads() {
    try {
        const response = await fetch('/api/downloads');
        const data = await response.json();
        
        if (response.ok && data.downloads) {
            data.downloads.forEach(task => {
                if (!['completed', 'failed'].includes(task.status)) {
                    addDownloadItem(task.id, task.url, task.service);
                }
            });
        }
    } catch (error) {
        console.error('Erreur lors du chargement des téléchargements:', error);
    }
}

// Ajouter un téléchargement à la liste
function addDownloadItem(taskId, url, service) {
    const downloadItems = document.querySelector('.download-items');
    
    if (!downloadItems) return;
    
    const item = document.createElement('div');
    item.className = 'download-item';
    item.dataset.taskId = taskId;
    
    item.innerHTML = `
        <div class="download-info">
            <span class="download-url">${truncateUrl(url)}</span>
            <span class="download-status">En attente...</span>
        </div>
        <div class="download-progress">
            <div class="progress-bar" style="width: 0%"></div>
        </div>
        <button class="btn btn-danger btn-sm cancel-download" data-task-id="${taskId}">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Ajouter les gestionnaires d'événements
    const cancelBtn = item.querySelector('.cancel-download');
    cancelBtn.addEventListener('click', () => cancelDownload(taskId));
    
    downloadItems.appendChild(item);
    
    // Démarrer le suivi de la progression
    startPolling(taskId);
}

// Suivre la progression du téléchargement
let activePolls = new Map();

function startPolling(taskId) {
    if (activePolls.has(taskId)) return;
    
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/downloads/${taskId}`);
            const data = await response.json();
            
            if (response.ok) {
                updateDownloadStatus(taskId, data);
                
                if (['completed', 'failed'].includes(data.status)) {
                    stopPolling(taskId);
                }
            } else {
                stopPolling(taskId);
                throw new Error(data.error || 'Erreur lors du suivi');
            }
        } catch (error) {
            console.error(`Erreur lors du suivi du téléchargement ${taskId}:`, error);
            stopPolling(taskId);
        }
    }, 1000);
    
    activePolls.set(taskId, pollInterval);
}

function stopPolling(taskId) {
    const interval = activePolls.get(taskId);
    if (interval) {
        clearInterval(interval);
        activePolls.delete(taskId);
    }
}

// Mettre à jour le statut d'un téléchargement
function updateDownloadStatus(taskId, data) {
    const item = document.querySelector(`[data-task-id="${taskId}"]`);
    if (!item) return;
    
    const statusEl = item.querySelector('.download-status');
    const progressBar = item.querySelector('.progress-bar');
    
    statusEl.textContent = getStatusText(data.status);
    progressBar.style.width = `${data.progress}%`;
    
    if (data.status === 'completed') {
        item.classList.add('completed');
        setTimeout(() => item.remove(), 5000);
        showNotification('Téléchargement terminé avec succès !', 'success');
    } else if (data.status === 'failed') {
        item.classList.add('failed');
        statusEl.textContent = `Erreur: ${data.error || 'Échec du téléchargement'}`;
        showNotification('Le téléchargement a échoué', 'error');
    }
}

// Annuler un téléchargement
async function cancelDownload(taskId) {
    try {
        const response = await fetch(`/api/downloads/${taskId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            stopPolling(taskId);
            const item = document.querySelector(`[data-task-id="${taskId}"]`);
            if (item) item.remove();
            showNotification('Téléchargement annulé', 'info');
        } else {
            throw new Error('Impossible d\'annuler le téléchargement');
        }
    } catch (error) {
        console.error('Erreur lors de l\'annulation:', error);
        showNotification(error.message, 'error');
    }
}

// Obtenir le texte du statut
function getStatusText(status) {
    const statusMap = {
        'pending': 'En attente...',
        'downloading': 'Téléchargement en cours...',
        'converting': 'Conversion en cours...',
        'completed': 'Terminé',
        'failed': 'Échec'
    };
    return statusMap[status] || status;
}

// Tronquer l'URL pour l'affichage
function truncateUrl(url) {
    const maxLength = 50;
    return url.length > maxLength
        ? url.substring(0, maxLength - 3) + '...'
        : url;
}

// Obtenir l'icône du service en fonction de l'URL
function getServiceIcon(url) {
    url = url.toLowerCase();
    
    if (url.includes('youtube.com') || url.includes('youtu.be')) {
        return 'fab fa-youtube';
    } else if (url.includes('spotify.com')) {
        return 'fab fa-spotify';
    } else if (url.includes('soundcloud.com')) {
        return 'fab fa-soundcloud';
    } else if (url.includes('deezer.com')) {
        return 'fas fa-music';
    } else {
        return 'fas fa-link';
    }
}

// Mettre à jour les statistiques
async function updateStats() {
    try {
        const response = await fetch(config.apiEndpoints.stats);
        
        if (!response.ok) {
            throw new Error('Erreur lors du chargement des statistiques');
        }
        
        const stats = await response.json();
        
        const totalTracksEl = document.getElementById('totalTracks');
        const totalArtistsEl = document.getElementById('totalArtists');
        const totalAlbumsEl = document.getElementById('totalAlbums');
        const totalPlaytimeEl = document.getElementById('totalPlaytime');
        
        if (totalTracksEl) totalTracksEl.textContent = stats.total_tracks || 0;
        if (totalArtistsEl) totalArtistsEl.textContent = stats.total_artists || 0;
        if (totalAlbumsEl) totalAlbumsEl.textContent = stats.total_albums || 0;
        if (totalPlaytimeEl) {
            const hours = Math.floor((stats.total_duration || 0) / 3600);
            const minutes = Math.floor(((stats.total_duration || 0) % 3600) / 60);
            totalPlaytimeEl.textContent = `${hours}h ${minutes}m`;
        }
    } catch (error) {
        console.error('Erreur lors du chargement des statistiques:', error);
    }
}

// Exporter les fonctions utiles
export { updateStats };
