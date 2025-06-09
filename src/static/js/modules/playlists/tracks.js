/**
 * Module Tracks - Gestion des pistes dans les playlists
 */

import { showNotification } from '../notifications.js';

// Configuration globale
let config;

// Charger les pistes d'une playlist
export async function loadPlaylistTracks(playlistId, appConfig) {
    if (appConfig) {
        config = appConfig;
    }
    
    try {
        const activePlaylist = document.getElementById('activePlaylist');
        const tracksContainer = document.getElementById('playlistTracks');
        
        if (!activePlaylist || !tracksContainer) return;
        
        // Afficher la section de playlist active
        activePlaylist.style.display = 'block';
        activePlaylist.dataset.playlistId = playlistId;
        
        // Afficher le chargement
        tracksContainer.innerHTML = `
            <tr>
                <td colspan="6" class="loading-cell">
                    <i class="fas fa-spinner fa-spin"></i> Chargement des pistes...
                </td>
            </tr>
        `;
        
        // Charger les pistes depuis l'API
        const response = await fetch(`${config.apiEndpoints.playlists}/${playlistId}/tracks`);
        
        if (!response.ok) {
            throw new Error('Erreur lors du chargement des pistes');
        }
        
        const tracks = await response.json();
        
        // Afficher les pistes
        displayPlaylistTracks(tracks, tracksContainer);
        
    } catch (error) {
        console.error('Erreur lors du chargement des pistes:', error);
        showNotification('Erreur lors du chargement des pistes', 'error');
    }
}

// Afficher les pistes d'une playlist
function displayPlaylistTracks(tracks, container) {
    if (!container) return;
    
    if (tracks.length === 0) {
        container.innerHTML = `
            <tr>
                <td colspan="6" class="empty-playlist">
                    <i class="fas fa-music"></i>
                    <p>Cette playlist est vide</p>
                    <button class="btn btn-primary add-tracks-btn">
                        <i class="fas fa-plus"></i> Ajouter des morceaux
                    </button>
                </td>
            </tr>
        `;
        
        const addTracksBtn = container.querySelector('.add-tracks-btn');
        if (addTracksBtn) {
            addTracksBtn.addEventListener('click', () => {
                // Rediriger vers la bibliothèque
                window.location.href = '/library';
            });
        }
        
        return;
    }
    
    // Vider le conteneur
    container.innerHTML = '';
    
    // Ajouter chaque piste
    tracks.forEach((track, index) => {
        const row = createTrackRow(track, index + 1);
        container.appendChild(row);
    });
}

// Créer une ligne de piste
function createTrackRow(track, position) {
    const row = document.createElement('tr');
    row.className = 'track-row';
    row.dataset.trackId = track.id;
    
    row.innerHTML = `
        <td class="position">
            <span class="track-number">${position}</span>
            <button class="play-btn">
                <i class="fas fa-play"></i>
            </button>
        </td>
        <td class="track-info">
            <div class="track-title">${track.title || 'Titre inconnu'}</div>
            <div class="track-source">
                <i class="${getSourceIcon(track.source)}"></i>
            </div>
        </td>
        <td class="track-artist">${track.artist || 'Artiste inconnu'}</td>
        <td class="track-album">${track.album || 'Album inconnu'}</td>
        <td class="track-duration">${formatDuration(track.duration)}</td>
        <td class="track-actions">
            <button class="btn btn-icon remove-track" title="Retirer de la playlist">
                <i class="fas fa-times"></i>
            </button>
        </td>
    `;
    
    // Ajouter les événements
    const playBtn = row.querySelector('.play-btn');
    if (playBtn) {
        playBtn.addEventListener('click', () => {
            if (window.playTrack) {
                window.playTrack(track);
            }
        });
    }
    
    const removeBtn = row.querySelector('.remove-track');
    if (removeBtn) {
        removeBtn.addEventListener('click', async () => {
            const playlistId = document.querySelector('.active-playlist').dataset.playlistId;
            await removeTrackFromPlaylist(track.id, playlistId);
        });
    }
    
    return row;
}

// Mettre à jour la vue d'une playlist
export function updatePlaylistView(playlist) {
    const playlistName = document.getElementById('playlistName');
    const playlistDescription = document.getElementById('playlistDescription');
    const playlistCover = document.getElementById('playlistCover');
    const playlistTrackCount = document.getElementById('playlistTrackCount');
    const playlistDuration = document.getElementById('playlistDuration');
    
    if (playlistName) {
        playlistName.textContent = playlist.name;
    }
    
    if (playlistDescription) {
        playlistDescription.textContent = playlist.description || '';
    }
    
    if (playlistCover) {
        if (playlist.cover_image) {
            playlistCover.style.backgroundImage = `url('${playlist.cover_image}')`;
            playlistCover.innerHTML = '';
        } else {
            playlistCover.style.backgroundImage = '';
            playlistCover.innerHTML = '<i class="fas fa-music"></i>';
        }
    }
    
    if (playlistTrackCount) {
        playlistTrackCount.textContent = `${playlist.track_count || 0} morceaux`;
    }
    
    if (playlistDuration) {
        playlistDuration.textContent = formatDuration(playlist.total_duration || 0);
    }
}

// Obtenir l'icône de la source
function getSourceIcon(source) {
    switch (source?.toLowerCase()) {
        case 'youtube':
            return 'fab fa-youtube';
        case 'spotify':
            return 'fab fa-spotify';
        case 'soundcloud':
            return 'fab fa-soundcloud';
        case 'deezer':
            return 'fas fa-music';
        default:
            return 'fas fa-music';
    }
}

// Formater la durée
function formatDuration(seconds) {
    if (!seconds) return '0:00';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

// Réordonner les pistes
export async function reorderPlaylistTracks(playlistId, trackId, newPosition) {
    try {
        const response = await fetch(`${config.apiEndpoints.playlists}/${playlistId}/tracks/reorder`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                track_id: trackId,
                position: newPosition
            })
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de la réorganisation des pistes');
        }
        
        // Recharger les pistes
        await loadPlaylistTracks(playlistId);
        
    } catch (error) {
        console.error('Erreur lors de la réorganisation des pistes:', error);
        showNotification('Erreur lors de la réorganisation des pistes', 'error');
    }
}
