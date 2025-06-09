/**
 * Gestion des téléchargements
 */

class Downloader {
    constructor() {
        this.form = document.getElementById('downloadForm');
        this.urlInput = document.getElementById('downloadUrl');
        this.serviceSelect = document.getElementById('downloadService');
        this.downloadsList = document.querySelector('.download-items');
        this.activeDownloads = new Map();
        this.pollInterval = 1000; // 1 seconde
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.startDownload();
        });
    }
    
    async startDownload() {
        const url = this.urlInput.value.trim();
        const service = this.serviceSelect.value;
        
        if (!url) return;
        
        try {
            const response = await fetch('/api/downloads', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url, service })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.addDownloadItem(data.task_id, url);
                this.urlInput.value = '';
                this.startPolling(data.task_id);
            } else {
                this.showError(data.error || 'Erreur lors du démarrage du téléchargement');
            }
        } catch (error) {
            this.showError('Erreur de connexion au serveur');
        }
    }
    
    addDownloadItem(taskId, url) {
        const item = document.createElement('div');
        item.className = 'download-item';
        item.dataset.taskId = taskId;
        
        item.innerHTML = `
            <div class="download-info">
                <span class="download-url">${this.truncateUrl(url)}</span>
                <span class="download-status">En attente...</span>
            </div>
            <div class="download-progress">
                <div class="progress-bar" style="width: 0%"></div>
            </div>
            <button class="btn btn-danger btn-sm cancel-download" data-task-id="${taskId}">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        item.querySelector('.cancel-download').addEventListener('click', () => {
            this.cancelDownload(taskId);
        });
        
        this.downloadsList.appendChild(item);
    }
    
    async startPolling(taskId) {
        if (this.activeDownloads.has(taskId)) return;
        
        const pollFn = async () => {
            try {
                const response = await fetch(`/api/downloads/${taskId}`);
                const data = await response.json();
                
                if (response.ok) {
                    this.updateDownloadStatus(taskId, data);
                    
                    if (['completed', 'failed'].includes(data.status)) {
                        this.stopPolling(taskId);
                    }
                } else {
                    this.stopPolling(taskId);
                }
            } catch (error) {
                console.error('Erreur lors de la récupération du statut:', error);
            }
        };
        
        this.activeDownloads.set(taskId, setInterval(pollFn, this.pollInterval));
        pollFn(); // Premier appel immédiat
    }
    
    stopPolling(taskId) {
        const interval = this.activeDownloads.get(taskId);
        if (interval) {
            clearInterval(interval);
            this.activeDownloads.delete(taskId);
        }
    }
    
    updateDownloadStatus(taskId, data) {
        const item = this.downloadsList.querySelector(`[data-task-id="${taskId}"]`);
        if (!item) return;
        
        const statusEl = item.querySelector('.download-status');
        const progressBar = item.querySelector('.progress-bar');
        
        statusEl.textContent = this.getStatusText(data.status);
        progressBar.style.width = `${data.progress}%`;
        
        if (data.status === 'completed') {
            item.classList.add('completed');
            setTimeout(() => item.remove(), 5000);
        } else if (data.status === 'failed') {
            item.classList.add('failed');
            statusEl.textContent = `Erreur: ${data.error || 'Échec du téléchargement'}`;
        }
    }
    
    async cancelDownload(taskId) {
        try {
            await fetch(`/api/downloads/${taskId}`, {
                method: 'DELETE'
            });
            
            this.stopPolling(taskId);
            const item = this.downloadsList.querySelector(`[data-task-id="${taskId}"]`);
            if (item) item.remove();
        } catch (error) {
            console.error('Erreur lors de l\'annulation:', error);
        }
    }
    
    getStatusText(status) {
        const statusMap = {
            'pending': 'En attente...',
            'downloading': 'Téléchargement en cours...',
            'converting': 'Conversion en cours...',
            'completed': 'Terminé',
            'failed': 'Échec'
        };
        return statusMap[status] || status;
    }
    
    truncateUrl(url) {
        const maxLength = 50;
        return url.length > maxLength
            ? url.substring(0, maxLength - 3) + '...'
            : url;
    }
    
    showError(message) {
        // TODO: Utiliser le système de notifications
        alert(message);
    }
}

// Initialiser le gestionnaire de téléchargements
document.addEventListener('DOMContentLoaded', () => {
    window.downloader = new Downloader();
});
