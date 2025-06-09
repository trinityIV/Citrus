/**
 * Gestion des streams (IPTV et Torrents) - scrapping only, aucune clé API requise
 */

class StreamManager {
    constructor() {
        this.activeStreams = new Map();
        this.videoPlayer = document.getElementById('video-player');
    }

    /**
     * Ajoute un stream IPTV
     */
    async addIPTVStream(url, name = '') {
        try {
            const response = await fetch('/stream/iptv/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url, name })
            });

            const data = await response.json();
            if (response.ok) {
                this.activeStreams.set(data.stream_id, {
                    type: 'iptv',
                    status: 'ready'
                });
                this.updateStreamsList();
                showNotification('Stream IPTV ajouté avec succès', 'success');
                return data.stream_id;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            showNotification(`Erreur: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Ajoute un stream torrent
     */
    async addTorrentStream(magnetOrFile, savePath = null) {
        try {
            let formData = new FormData();
            let url = '/stream/torrent/add';
            let options = {
                method: 'POST'
            };

            if (typeof magnetOrFile === 'string') {
                // Lien magnet
                options.headers = {
                    'Content-Type': 'application/json'
                };
                options.body = JSON.stringify({
                    magnet: magnetOrFile,
                    save_path: savePath
                });
            } else {
                // Fichier torrent
                formData.append('torrent', magnetOrFile);
                if (savePath) formData.append('save_path', savePath);
                options.body = formData;
            }

            const response = await fetch(url, options);
            const data = await response.json();

            if (response.ok) {
                this.activeStreams.set(data.stream_id, {
                    type: 'torrent',
                    status: 'downloading',
                    progress: 0
                });
                this.updateStreamsList();
                this.monitorTorrentProgress(data.stream_id);
                showNotification('Torrent ajouté avec succès', 'success');
                return data.stream_id;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            showNotification(`Erreur: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Surveille la progression d'un torrent
     */
    async monitorTorrentProgress(streamId) {
        while (this.activeStreams.has(streamId)) {
            try {
                const response = await fetch(`/stream/${streamId}/status`);
                const status = await response.json();

                if (response.ok) {
                    this.activeStreams.set(streamId, status);
                    this.updateStreamProgress(streamId, status);

                    if (status.status === 'completed') {
                        showNotification('Téléchargement terminé', 'success');
                        break;
                    }
                } else {
                    throw new Error(status.error);
                }
            } catch (error) {
                console.error('Erreur de surveillance:', error);
            }

            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }

    /**
     * Met à jour l'affichage de la progression
     */
    updateStreamProgress(streamId, status) {
        const progressElement = document.querySelector(`#stream-${streamId} .progress`);
        if (progressElement) {
            progressElement.style.width = `${status.progress}%`;
            progressElement.textContent = `${Math.round(status.progress)}%`;
        }

        const statsElement = document.querySelector(`#stream-${streamId} .stats`);
        if (statsElement && status.type === 'torrent') {
            statsElement.textContent = `↓ ${this.formatSpeed(status.download_rate)} ↑ ${this.formatSpeed(status.upload_rate)} | Peers: ${status.num_peers}`;
        }
    }

    /**
     * Formate la vitesse en unités lisibles
     */
    formatSpeed(bytesPerSecond) {
        const units = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
        let speed = bytesPerSecond;
        let unitIndex = 0;
        
        while (speed >= 1024 && unitIndex < units.length - 1) {
            speed /= 1024;
            unitIndex++;
        }
        
        return `${speed.toFixed(1)} ${units[unitIndex]}`;
    }

    /**
     * Arrête un stream
     */
    async stopStream(streamId) {
        try {
            const response = await fetch(`/stream/${streamId}/stop`, {
                method: 'POST'
            });
            
            const data = await response.json();
            if (response.ok) {
                this.activeStreams.delete(streamId);
                this.updateStreamsList();
                showNotification('Stream arrêté avec succès', 'success');
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            showNotification(`Erreur: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Lit un stream
     */
    async playStream(streamId) {
        try {
            const stream = this.activeStreams.get(streamId);
            if (!stream) throw new Error('Stream non trouvé');

            // Mettre à jour le lecteur vidéo
            this.videoPlayer.src = `/stream/${streamId}/play`;
            await this.videoPlayer.play();
        } catch (error) {
            showNotification(`Erreur de lecture: ${error.message}`, 'error');
            throw error;
        }
    }

    /**
     * Met à jour la liste des streams dans l'interface
     */
    updateStreamsList() {
        const container = document.getElementById('streams-list');
        if (!container) return;

        container.innerHTML = '';
        this.activeStreams.forEach((stream, id) => {
            const element = document.createElement('div');
            element.id = `stream-${id}`;
            element.className = 'stream-item';
            
            let html = `
                <div class="stream-info">
                    <span class="type">${stream.type}</span>
                    <span class="status">${stream.status}</span>
                </div>
            `;

            if (stream.type === 'torrent' && stream.status === 'downloading') {
                html += `
                    <div class="progress-bar">
                        <div class="progress" style="width: ${stream.progress}%">
                            ${Math.round(stream.progress)}%
                        </div>
                    </div>
                    <div class="stats"></div>
                `;
            }

            html += `
                <div class="controls">
                    <button onclick="streamManager.playStream(${id})">
                        <i class="fas fa-play"></i>
                    </button>
                    <button onclick="streamManager.stopStream(${id})">
                        <i class="fas fa-stop"></i>
                    </button>
                </div>
            `;

            element.innerHTML = html;
            container.appendChild(element);
        });
    }
}

// Créer l'instance du gestionnaire de streams
const streamManager = new StreamManager();

// Gestionnaires d'événements pour l'interface utilisateur
document.addEventListener('DOMContentLoaded', () => {
    // Formulaire d'ajout IPTV
    const iptvForm = document.getElementById('iptv-form');
    if (iptvForm) {
        iptvForm.onsubmit = async (e) => {
            e.preventDefault();
            const url = document.getElementById('iptv-url').value;
            const name = document.getElementById('iptv-name').value;
            await streamManager.addIPTVStream(url, name);
        };
    }

    // Formulaire d'ajout Torrent
    const torrentForm = document.getElementById('torrent-form');
    if (torrentForm) {
        torrentForm.onsubmit = async (e) => {
            e.preventDefault();
            const magnetInput = document.getElementById('torrent-magnet');
            const fileInput = document.getElementById('torrent-file');
            const savePath = document.getElementById('save-path').value;

            if (magnetInput.value) {
                await streamManager.addTorrentStream(magnetInput.value, savePath);
            } else if (fileInput.files.length > 0) {
                await streamManager.addTorrentStream(fileInput.files[0], savePath);
            }
        };
    }
});
