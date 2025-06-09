/**
 * Module Playlists - Point d'entrée pour la gestion des playlists
 */

import { initModal } from './modal.js';
import { initPlaylistActions } from './actions.js';
import { loadPlaylistTracks, updatePlaylistView } from './tracks.js';
import { showNotification } from '../notifications.js';

// Configuration globale
let config;

// Initialisation du module playlists
export function initPlaylists(appConfig) {
    config = appConfig;
    
    // Initialiser la modal
    initModal();
    
    // Initialiser les actions des playlists
    initPlaylistActions(config);
    
    // Initialiser les événements
    initEvents();
}

// Initialisation des événements
function initEvents() {
    const createPlaylistBtn = document.getElementById('createPlaylistBtn');
    
    if (createPlaylistBtn) {
        createPlaylistBtn.addEventListener('click', () => {
            const modal = document.getElementById('playlistModal');
            if (modal) {
                modal.style.display = 'block';
                // Réinitialiser le formulaire
                document.getElementById('playlistForm').reset();
                document.getElementById('modalTitle').textContent = 'Nouvelle Playlist';
                document.getElementById('coverPreview').style.backgroundImage = '';
            }
        });
    }
}

// Charger toutes les playlists
export async function loadPlaylists() {
    try {
        const playlistsGrid = document.getElementById('playlistsGrid');
        
        if (!playlistsGrid) return;
        
        // Afficher le chargement
        playlistsGrid.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Chargement des playlists...</div>';
        
        // Charger les playlists depuis l'API
        const response = await fetch(config.apiEndpoints.playlists);
        
        if (!response.ok) {
            throw new Error('Erreur lors du chargement des playlists');
        }
        
        const playlists = await response.json();
        
        // Afficher les playlists
        displayPlaylists(playlists, playlistsGrid);
        
    } catch (error) {
        console.error('Erreur lors du chargement des playlists:', error);
        showNotification('Erreur lors du chargement des playlists', 'error');
    }
}

// Afficher les playlists dans la grille
function displayPlaylists(playlists, container) {
    if (!container) return;
    
    if (playlists.length === 0) {
        container.innerHTML = `
            <div class="no-playlists">
                <i class="fas fa-music"></i>
                <p>Vous n'avez pas encore de playlist</p>
                <button id="createFirstPlaylistBtn" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Créer ma première playlist
                </button>
            </div>
        `;
        
        const createFirstPlaylistBtn = document.getElementById('createFirstPlaylistBtn');
        if (createFirstPlaylistBtn) {
            createFirstPlaylistBtn.addEventListener('click', () => {
                const modal = document.getElementById('playlistModal');
                if (modal) {
                    modal.style.display = 'block';
                }
            });
        }
        
        return;
    }
    
    // Vider le conteneur
    container.innerHTML = '';
    
    // Créer la grille
    const grid = document.createElement('div');
    grid.className = 'playlists-grid';
    
    // Ajouter chaque playlist
    playlists.forEach((playlist, index) => {
        const playlistElement = createPlaylistElement(playlist, index);
        grid.appendChild(playlistElement);
    });
    
    // Ajouter la grille au conteneur
    container.appendChild(grid);
}

// Créer un élément de playlist
function createPlaylistElement(playlist, index) {
    const template = document.getElementById('playlistTemplate');
    const element = template.content.cloneNode(true);
    
    const playlistCard = element.querySelector('.playlist-card');
    const playlistCover = element.querySelector('.playlist-cover');
    const playlistName = element.querySelector('.playlist-name');
    const playlistTracksCount = element.querySelector('.playlist-tracks-count');
    
    // Définir les données
    playlistCard.dataset.playlistId = playlist.id;
    playlistCard.style.animationDelay = `${index * 0.1}s`;
    
    if (playlist.cover_image) {
        playlistCover.style.backgroundImage = `url('${playlist.cover_image}')`;
    } else {
        playlistCover.innerHTML = '<i class="fas fa-music"></i>';
    }
    
    playlistName.textContent = playlist.name;
    playlistTracksCount.textContent = `${playlist.track_count || 0} morceaux`;
    
    // Ajouter les événements
    playlistCard.addEventListener('click', () => {
        loadPlaylistTracks(playlist.id, config);
        updatePlaylistView(playlist);
    });
    
    return element;
}

// Exporter les fonctions nécessaires
export { loadPlaylistTracks, updatePlaylistView };
