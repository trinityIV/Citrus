/**
 * Module Library - Gestion de la bibliothèque musicale
 */

import { showNotification } from './notifications.js';

// Configuration globale
let config;

// Initialisation de la bibliothèque
export function initLibrary(appConfig) {
    config = appConfig;
    
    // Charger les dernières pistes
    loadRecentTracks();
    
    // Initialiser la recherche
    initSearch();
    
    // Initialiser les filtres
    initFilters();
}

// Charger les dernières pistes
export async function loadRecentTracks() {
    try {
        const response = await fetch(`${config.apiEndpoints.library}?limit=6`);
        
        if (!response.ok) {
            throw new Error('Erreur lors du chargement des pistes');
        }
        
        const tracks = await response.json();
        const tracksContainer = document.getElementById('recentTracks');
        
        if (!tracksContainer) return;
        
        if (tracks.length === 0) {
            tracksContainer.innerHTML = '<p class="no-tracks">Aucune musique trouvée. Commencez par télécharger de la musique !</p>';
            return;
        }
        
        // Vider le conteneur
        tracksContainer.innerHTML = '';
        
        // Ajouter chaque piste au conteneur
        tracks.forEach((track, index) => {
            const trackElement = document.createElement('div');
            trackElement.className = 'track-card';
            trackElement.style.animationDelay = `${index * 0.1}s`;
            
            trackElement.innerHTML = `
                <div class="track-cover" style="background-image: url('${track.cover_art || ''}')">
                    ${!track.cover_art ? '<i class="fas fa-music"></i>' : ''}
                    <div class="track-overlay">
                        <div class="play-btn" data-track-id="${track.id}">
                            <i class="fas fa-play"></i>
                        </div>
                    </div>
                </div>
                <div class="track-info">
                    <div class="track-title">${track.title || 'Titre inconnu'}</div>
                    <div class="track-artist">${track.artist || 'Artiste inconnu'}</div>
                </div>
            `;
            
            // Ajouter un écouteur d'événements pour la lecture
            const playBtn = trackElement.querySelector('.play-btn');
            if (playBtn) {
                playBtn.addEventListener('click', () => {
                    const trackId = playBtn.getAttribute('data-track-id');
                    playTrackById(trackId, tracks);
                });
            }
            
            tracksContainer.appendChild(trackElement);
        });
        
    } catch (error) {
        console.error('Erreur lors du chargement des dernières musiques:', error);
        showNotification('Erreur lors du chargement de la bibliothèque', 'error');
    }
}

// Jouer une piste par ID
function playTrackById(trackId, tracksList) {
    const track = tracksList.find(t => t.id === trackId);
    
    if (track && window.playTrack) {
        window.playTrack(track);
    } else {
        showNotification('Impossible de lire cette piste', 'error');
    }
}

// Initialiser la recherche
function initSearch() {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    
    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const query = searchInput.value.trim();
            
            if (!query) {
                return;
            }
            
            try {
                // Afficher l'indicateur de chargement
                if (searchResults) {
                    searchResults.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Recherche en cours...</div>';
                    searchResults.style.display = 'block';
                }
                
                // Effectuer la recherche
                const response = await fetch(`${config.apiEndpoints.library}/search?q=${encodeURIComponent(query)}`);
                
                if (!response.ok) {
                    throw new Error('Erreur lors de la recherche');
                }
                
                const results = await response.json();
                
                // Afficher les résultats
                displaySearchResults(results, searchResults);
                
            } catch (error) {
                console.error('Erreur lors de la recherche:', error);
                
                if (searchResults) {
                    searchResults.innerHTML = '<div class="error">Erreur lors de la recherche. Veuillez réessayer.</div>';
                }
            }
        });
        
        // Fermer les résultats lors du clic à l'extérieur
        document.addEventListener('click', (e) => {
            if (searchResults && !searchForm.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.style.display = 'none';
            }
        });
    }
}

// Afficher les résultats de recherche
function displaySearchResults(results, container) {
    if (!container) return;
    
    if (results.length === 0) {
        container.innerHTML = '<div class="no-results">Aucun résultat trouvé</div>';
        return;
    }
    
    // Limiter le nombre de résultats affichés
    const limitedResults = results.slice(0, 10);
    
    // Créer la liste des résultats
    const resultsList = document.createElement('ul');
    resultsList.className = 'search-results-list';
    
    limitedResults.forEach(track => {
        const resultItem = document.createElement('li');
        resultItem.className = 'search-result-item';
        
        resultItem.innerHTML = `
            <div class="result-cover" style="background-image: url('${track.cover_art || ''}')">
                ${!track.cover_art ? '<i class="fas fa-music"></i>' : ''}
            </div>
            <div class="result-info">
                <div class="result-title">${track.title || 'Titre inconnu'}</div>
                <div class="result-artist">${track.artist || 'Artiste inconnu'}</div>
            </div>
            <div class="result-actions">
                <button class="play-btn" data-track-id="${track.id}">
                    <i class="fas fa-play"></i>
                </button>
            </div>
        `;
        
        // Ajouter un écouteur d'événements pour la lecture
        const playBtn = resultItem.querySelector('.play-btn');
        if (playBtn) {
            playBtn.addEventListener('click', () => {
                const trackId = playBtn.getAttribute('data-track-id');
                playTrackById(trackId, results);
                container.style.display = 'none';
            });
        }
        
        resultsList.appendChild(resultItem);
    });
    
    // Ajouter un lien "Voir tous les résultats" si nécessaire
    if (results.length > 10) {
        const viewAllItem = document.createElement('li');
        viewAllItem.className = 'view-all-results';
        viewAllItem.innerHTML = `<a href="/library?q=${encodeURIComponent(document.getElementById('searchInput').value)}">Voir tous les résultats (${results.length})</a>`;
        resultsList.appendChild(viewAllItem);
    }
    
    // Vider et remplir le conteneur
    container.innerHTML = '';
    container.appendChild(resultsList);
}

// Initialiser les filtres
function initFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const sortSelect = document.getElementById('sortSelect');
    
    // Filtres par catégorie
    if (filterButtons.length > 0) {
        filterButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const filter = btn.getAttribute('data-filter');
                
                // Retirer la classe active de tous les boutons
                filterButtons.forEach(b => b.classList.remove('active'));
                
                // Ajouter la classe active au bouton cliqué
                btn.classList.add('active');
                
                // Appliquer le filtre
                applyFilters(filter, sortSelect ? sortSelect.value : 'newest');
            });
        });
    }
    
    // Tri
    if (sortSelect) {
        sortSelect.addEventListener('change', () => {
            const activeFilter = document.querySelector('.filter-btn.active');
            const filter = activeFilter ? activeFilter.getAttribute('data-filter') : 'all';
            
            applyFilters(filter, sortSelect.value);
        });
    }
}

// Appliquer les filtres
async function applyFilters(filter, sort) {
    try {
        const libraryContainer = document.getElementById('libraryTracks');
        
        if (!libraryContainer) return;
        
        // Afficher l'indicateur de chargement
        libraryContainer.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> Chargement...</div>';
        
        // Construire l'URL avec les paramètres
        let url = `${config.apiEndpoints.library}?`;
        
        if (filter && filter !== 'all') {
            url += `filter=${encodeURIComponent(filter)}&`;
        }
        
        if (sort) {
            url += `sort=${encodeURIComponent(sort)}`;
        }
        
        // Effectuer la requête
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error('Erreur lors du chargement des pistes');
        }
        
        const tracks = await response.json();
        
        // Afficher les pistes
        displayLibraryTracks(tracks, libraryContainer);
        
    } catch (error) {
        console.error('Erreur lors de l\'application des filtres:', error);
        showNotification('Erreur lors du chargement de la bibliothèque', 'error');
    }
}

// Afficher les pistes de la bibliothèque
function displayLibraryTracks(tracks, container) {
    if (!container) return;
    
    if (tracks.length === 0) {
        container.innerHTML = '<div class="no-tracks">Aucune musique trouvée</div>';
        return;
    }
    
    // Vider le conteneur
    container.innerHTML = '';
    
    // Créer la grille de pistes
    const tracksGrid = document.createElement('div');
    tracksGrid.className = 'tracks-grid';
    
    // Ajouter chaque piste à la grille
    tracks.forEach((track, index) => {
        const trackElement = document.createElement('div');
        trackElement.className = 'track-card';
        trackElement.style.animationDelay = `${index * 0.05}s`;
        
        trackElement.innerHTML = `
            <div class="track-cover" style="background-image: url('${track.cover_art || ''}')">
                ${!track.cover_art ? '<i class="fas fa-music"></i>' : ''}
                <div class="track-overlay">
                    <div class="play-btn" data-track-id="${track.id}">
                        <i class="fas fa-play"></i>
                    </div>
                </div>
            </div>
            <div class="track-info">
                <div class="track-title">${track.title || 'Titre inconnu'}</div>
                <div class="track-artist">${track.artist || 'Artiste inconnu'}</div>
                <div class="track-album">${track.album || 'Album inconnu'}</div>
            </div>
        `;
        
        // Ajouter un écouteur d'événements pour la lecture
        const playBtn = trackElement.querySelector('.play-btn');
        if (playBtn) {
            playBtn.addEventListener('click', () => {
                const trackId = playBtn.getAttribute('data-track-id');
                playTrackById(trackId, tracks);
            });
        }
        
        tracksGrid.appendChild(trackElement);
    });
    
    // Ajouter la grille au conteneur
    container.appendChild(tracksGrid);
}
