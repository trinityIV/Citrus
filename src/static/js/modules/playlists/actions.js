/**
 * Module Actions - Gestion des actions sur les playlists
 */

import { showNotification } from '../notifications.js';
import { openEditModal } from './modal.js';

// Configuration globale
let config;

// Initialisation des actions des playlists
export function initPlaylistActions(appConfig) {
    config = appConfig;
    
    // Initialiser les boutons d'action
    initActionButtons();
}

// Initialiser les boutons d'action
function initActionButtons() {
    const playPlaylistBtn = document.getElementById('playPlaylistBtn');
    const shufflePlaylistBtn = document.getElementById('shufflePlaylistBtn');
    const editPlaylistBtn = document.getElementById('editPlaylistBtn');
    const deletePlaylistBtn = document.getElementById('deletePlaylistBtn');
    
    if (playPlaylistBtn) {
        playPlaylistBtn.addEventListener('click', () => {
            const playlistId = document.querySelector('.active-playlist').dataset.playlistId;
            playPlaylist(playlistId);
        });
    }
    
    if (shufflePlaylistBtn) {
        shufflePlaylistBtn.addEventListener('click', () => {
            const playlistId = document.querySelector('.active-playlist').dataset.playlistId;
            playPlaylist(playlistId, true);
        });
    }
    
    if (editPlaylistBtn) {
        editPlaylistBtn.addEventListener('click', () => {
            const playlistId = document.querySelector('.active-playlist').dataset.playlistId;
            editPlaylist(playlistId);
        });
    }
    
    if (deletePlaylistBtn) {
        deletePlaylistBtn.addEventListener('click', () => {
            const playlistId = document.querySelector('.active-playlist').dataset.playlistId;
            deletePlaylist(playlistId);
        });
    }
}

// Jouer une playlist
async function playPlaylist(playlistId, shuffle = false) {
    try {
        const response = await fetch(`${config.apiEndpoints.playlists}/${playlistId}/tracks`);
        
        if (!response.ok) {
            throw new Error('Erreur lors du chargement de la playlist');
        }
        
        const tracks = await response.json();
        
        if (tracks.length === 0) {
            showNotification('Cette playlist est vide', 'warning');
            return;
        }
        
        // Si le mode aléatoire est activé, mélanger les pistes
        if (shuffle) {
            shuffleArray(tracks);
        }
        
        // Jouer la première piste
        if (window.playTrack) {
            window.playTrack(tracks[0]);
            
            // Sauvegarder la playlist dans le lecteur
            if (window.setCurrentPlaylist) {
                window.setCurrentPlaylist(tracks, playlistId);
            }
        }
        
    } catch (error) {
        console.error('Erreur lors de la lecture de la playlist:', error);
        showNotification('Erreur lors de la lecture de la playlist', 'error');
    }
}

// Éditer une playlist
async function editPlaylist(playlistId) {
    try {
        const response = await fetch(`${config.apiEndpoints.playlists}/${playlistId}`);
        
        if (!response.ok) {
            throw new Error('Erreur lors du chargement de la playlist');
        }
        
        const playlist = await response.json();
        
        // Ouvrir la modal d'édition
        openEditModal(playlist);
        
    } catch (error) {
        console.error('Erreur lors du chargement de la playlist:', error);
        showNotification('Erreur lors du chargement de la playlist', 'error');
    }
}

// Supprimer une playlist
async function deletePlaylist(playlistId) {
    // Demander confirmation
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette playlist ?')) {
        return;
    }
    
    try {
        const response = await fetch(`${config.apiEndpoints.playlists}/${playlistId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de la suppression de la playlist');
        }
        
        // Afficher une notification de succès
        showNotification('Playlist supprimée avec succès', 'success');
        
        // Masquer la vue active
        const activePlaylist = document.getElementById('activePlaylist');
        if (activePlaylist) {
            activePlaylist.style.display = 'none';
        }
        
        // Recharger la liste des playlists
        if (window.loadPlaylists) {
            window.loadPlaylists();
        }
        
    } catch (error) {
        console.error('Erreur lors de la suppression de la playlist:', error);
        showNotification('Erreur lors de la suppression de la playlist', 'error');
    }
}

// Mélanger un tableau
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

// Ajouter une piste à une playlist
export async function addTrackToPlaylist(trackId, playlistId) {
    try {
        const response = await fetch(`${config.apiEndpoints.playlists}/${playlistId}/tracks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ track_id: trackId })
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de l\'ajout de la piste');
        }
        
        // Afficher une notification de succès
        showNotification('Piste ajoutée à la playlist', 'success');
        
        // Si la playlist est actuellement affichée, la recharger
        const activePlaylist = document.querySelector('.active-playlist');
        if (activePlaylist && activePlaylist.dataset.playlistId === playlistId) {
            const tracks = document.getElementById('playlistTracks');
            if (tracks) {
                loadPlaylistTracks(playlistId);
            }
        }
        
    } catch (error) {
        console.error('Erreur lors de l\'ajout de la piste:', error);
        showNotification('Erreur lors de l\'ajout de la piste', 'error');
    }
}

// Supprimer une piste d'une playlist
export async function removeTrackFromPlaylist(trackId, playlistId) {
    try {
        const response = await fetch(`${config.apiEndpoints.playlists}/${playlistId}/tracks/${trackId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de la suppression de la piste');
        }
        
        // Afficher une notification de succès
        showNotification('Piste supprimée de la playlist', 'success');
        
        // Si la playlist est actuellement affichée, la recharger
        const activePlaylist = document.querySelector('.active-playlist');
        if (activePlaylist && activePlaylist.dataset.playlistId === playlistId) {
            const tracks = document.getElementById('playlistTracks');
            if (tracks) {
                loadPlaylistTracks(playlistId);
            }
        }
        
    } catch (error) {
        console.error('Erreur lors de la suppression de la piste:', error);
        showNotification('Erreur lors de la suppression de la piste', 'error');
    }
}
