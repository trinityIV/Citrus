/**
 * Gestion des téléchargements de fichiers audio
 */

class DownloadManager {
    /**
     * Télécharge une piste dans le format spécifié
     * @param {number} trackId - ID de la piste
     * @param {string} format - Format audio (mp3, wav, ogg, flac)
     */
    static async downloadTrack(trackId, format = 'mp3') {
        try {
            // Créer l'URL de téléchargement
            const url = `/download/${trackId}?format=${format}`;
            
            // Créer un lien temporaire et cliquer dessus
            const link = document.createElement('a');
            link.href = url;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Afficher une notification de succès
            showNotification('Téléchargement démarré', 'success');
            
        } catch (error) {
            console.error('Erreur de téléchargement:', error);
            showNotification('Erreur lors du téléchargement', 'error');
        }
    }

    /**
     * Télécharge une playlist entière au format ZIP
     * @param {number} playlistId - ID de la playlist
     * @param {string} format - Format audio pour les fichiers (mp3, wav, ogg, flac)
     */
    static async downloadPlaylist(playlistId, format = 'mp3') {
        try {
            const url = `/download/playlist/${playlistId}?format=${format}`;
            
            // Créer un lien temporaire et cliquer dessus
            const link = document.createElement('a');
            link.href = url;
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            showNotification('Téléchargement de la playlist démarré', 'success');
            
        } catch (error) {
            console.error('Erreur de téléchargement:', error);
            showNotification('Erreur lors du téléchargement de la playlist', 'error');
        }
    }
}

// Ajouter les boutons de téléchargement aux pistes
document.addEventListener('DOMContentLoaded', () => {
    // Ajouter les boutons de téléchargement à chaque piste
    const tracks = document.querySelectorAll('.track-item');
    tracks.forEach(track => {
        const trackId = track.dataset.trackId;
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'download-btn';
        downloadBtn.innerHTML = '<i class="fas fa-download"></i>';
        downloadBtn.onclick = () => {
            // Afficher un menu pour choisir le format
            const format = prompt('Choisir le format (mp3, wav, ogg, flac):', 'mp3');
            if (format) {
                DownloadManager.downloadTrack(trackId, format);
            }
        };
        track.appendChild(downloadBtn);
    });

    // Ajouter les boutons de téléchargement aux playlists
    const playlists = document.querySelectorAll('.playlist-item');
    playlists.forEach(playlist => {
        const playlistId = playlist.dataset.playlistId;
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'download-playlist-btn';
        downloadBtn.innerHTML = '<i class="fas fa-download"></i> Télécharger tout';
        downloadBtn.onclick = () => {
            const format = prompt('Choisir le format (mp3, wav, ogg, flac):', 'mp3');
            if (format) {
                DownloadManager.downloadPlaylist(playlistId, format);
            }
        };
        playlist.appendChild(downloadBtn);
    });
});
