/**
 * Gestion des métadonnées et des playlists
 */

class MetadataManager {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Formulaire d'édition de métadonnées
        const metadataForm = document.getElementById('metadata-form');
        if (metadataForm) {
            metadataForm.addEventListener('submit', this.handleMetadataEdit.bind(this));
        }

        // Formulaire de création de playlist
        const playlistForm = document.getElementById('playlist-form');
        if (playlistForm) {
            playlistForm.addEventListener('submit', this.handlePlaylistCreate.bind(this));
        }

        // Glisser-déposer pour les fichiers
        const dropZones = document.querySelectorAll('.file-drop-zone');
        dropZones.forEach(zone => {
            zone.addEventListener('dragover', this.handleDragOver.bind(this));
            zone.addEventListener('drop', this.handleDrop.bind(this));
        });
    }

    async handleMetadataEdit(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);

        try {
            const response = await fetch('/metadata/edit', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            if (response.ok) {
                showNotification('Métadonnées mises à jour avec succès', 'success');
                this.updateMetadataDisplay(result);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            showNotification(`Erreur: ${error.message}`, 'error');
        }
    }

    async handlePlaylistCreate(event) {
        event.preventDefault();
        const form = event.target;
        const data = {
            name: form.querySelector('#playlist-name').value,
            description: form.querySelector('#playlist-description').value
        };

        try {
            const response = await fetch('/playlists', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            if (response.ok) {
                showNotification('Playlist créée avec succès', 'success');
                this.refreshPlaylistsList();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            showNotification(`Erreur: ${error.message}`, 'error');
        }
    }

    handleDragOver(event) {
        event.preventDefault();
        event.currentTarget.classList.add('drag-over');
    }

    async handleDrop(event) {
        event.preventDefault();
        event.currentTarget.classList.remove('drag-over');

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            const formData = new FormData();
            formData.append('file', files[0]);

            try {
                // Extraire les métadonnées automatiquement
                const response = await fetch('/metadata/extract', {
                    method: 'POST',
                    body: formData
                });

                const metadata = await response.json();
                if (response.ok) {
                    this.populateMetadataForm(metadata);
                } else {
                    throw new Error(metadata.error);
                }
            } catch (error) {
                showNotification(`Erreur: ${error.message}`, 'error');
            }
        }
    }

    populateMetadataForm(metadata) {
        const form = document.getElementById('metadata-form');
        if (!form) return;

        // Remplir les champs du formulaire
        for (const [key, value] of Object.entries(metadata)) {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = value;
            }
        }

        // Afficher la couverture si présente
        if (metadata.cover) {
            const coverPreview = document.getElementById('cover-preview');
            if (coverPreview) {
                coverPreview.src = metadata.cover;
                coverPreview.style.display = 'block';
            }
        }
    }

    async refreshPlaylistsList() {
        try {
            const response = await fetch('/playlists');
            const playlists = await response.json();

            const container = document.getElementById('playlists-container');
            if (!container) return;

            container.innerHTML = playlists.map(playlist => `
                <div class="playlist-card" data-id="${playlist.id}">
                    <h3>${playlist.name}</h3>
                    <p>${playlist.description}</p>
                    <div class="playlist-stats">
                        <span>${playlist.track_count} pistes</span>
                        <span>Mis à jour le ${new Date(playlist.updated_at).toLocaleDateString()}</span>
                    </div>
                    <div class="playlist-controls">
                        <button onclick="metadataManager.editPlaylist('${playlist.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="metadataManager.deletePlaylist('${playlist.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            showNotification(`Erreur: ${error.message}`, 'error');
        }
    }

    async editPlaylist(playlistId) {
        try {
            const response = await fetch(`/playlists/${playlistId}`);
            const playlist = await response.json();

            if (response.ok) {
                // Ouvrir le modal d'édition
                const modal = document.getElementById('edit-playlist-modal');
                if (modal) {
                    modal.querySelector('#edit-playlist-name').value = playlist.name;
                    modal.querySelector('#edit-playlist-description').value = playlist.description;
                    modal.querySelector('#edit-playlist-id').value = playlist.id;
                    modal.style.display = 'block';
                }
            } else {
                throw new Error(playlist.error);
            }
        } catch (error) {
            showNotification(`Erreur: ${error.message}`, 'error');
        }
    }

    async deletePlaylist(playlistId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cette playlist ?')) {
            return;
        }

        try {
            const response = await fetch(`/playlists/${playlistId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                showNotification('Playlist supprimée avec succès', 'success');
                this.refreshPlaylistsList();
            } else {
                const result = await response.json();
                throw new Error(result.error);
            }
        } catch (error) {
            showNotification(`Erreur: ${error.message}`, 'error');
        }
    }

    updateMetadataDisplay(metadata) {
        const display = document.getElementById('metadata-display');
        if (!display) return;

        display.innerHTML = `
            <div class="metadata-card">
                <div class="metadata-header">
                    ${metadata.cover ? `<img src="${metadata.cover}" alt="Cover" class="cover-image">` : ''}
                    <h2>${metadata.title || 'Sans titre'}</h2>
                </div>
                <div class="metadata-content">
                    <p><strong>Artiste:</strong> ${metadata.artist || 'Inconnu'}</p>
                    <p><strong>Album:</strong> ${metadata.album || 'Inconnu'}</p>
                    <p><strong>Genre:</strong> ${metadata.genre || 'Non spécifié'}</p>
                    <p><strong>Année:</strong> ${metadata.year || 'Non spécifiée'}</p>
                    <p><strong>Piste:</strong> ${metadata.track_num || 'Non spécifié'}</p>
                    ${metadata.lyrics ? `<div class="lyrics">${metadata.lyrics}</div>` : ''}
                </div>
            </div>
        `;
    }
}

// Créer l'instance du gestionnaire de métadonnées
const metadataManager = new MetadataManager();
