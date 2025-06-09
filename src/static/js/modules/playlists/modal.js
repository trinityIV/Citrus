/**
 * Module Modal - Gestion de la modal des playlists
 */

import { showNotification } from '../notifications.js';

// Initialisation de la modal
export function initModal() {
    const modal = document.getElementById('playlistModal');
    const form = document.getElementById('playlistForm');
    const closeBtn = modal.querySelector('.close-modal');
    const cancelBtn = document.getElementById('cancelPlaylistBtn');
    const coverInput = document.getElementById('playlistCoverInput');
    
    // Fermer la modal
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    // Fermer la modal en cliquant à l'extérieur
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Gérer la prévisualisation de l'image de couverture
    if (coverInput) {
        coverInput.addEventListener('change', handleCoverPreview);
    }
    
    // Gérer la soumission du formulaire
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
}

// Gérer la prévisualisation de l'image de couverture
function handleCoverPreview(e) {
    const file = e.target.files[0];
    const preview = document.getElementById('coverPreview');
    
    if (!file || !preview) return;
    
    // Vérifier le type de fichier
    if (!file.type.startsWith('image/')) {
        showNotification('Veuillez sélectionner une image', 'error');
        e.target.value = '';
        return;
    }
    
    // Vérifier la taille du fichier (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        showNotification('L\'image ne doit pas dépasser 5MB', 'error');
        e.target.value = '';
        return;
    }
    
    // Afficher la prévisualisation
    const reader = new FileReader();
    
    reader.onload = (e) => {
        preview.style.backgroundImage = `url('${e.target.result}')`;
    };
    
    reader.onerror = () => {
        showNotification('Erreur lors de la lecture de l\'image', 'error');
        e.target.value = '';
    };
    
    reader.readAsDataURL(file);
}

// Gérer la soumission du formulaire
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const modal = document.getElementById('playlistModal');
    const nameInput = document.getElementById('playlistNameInput');
    const descInput = document.getElementById('playlistDescInput');
    const coverInput = document.getElementById('playlistCoverInput');
    
    if (!nameInput || !descInput || !coverInput) return;
    
    try {
        // Créer un objet FormData
        const formData = new FormData();
        formData.append('name', nameInput.value.trim());
        formData.append('description', descInput.value.trim());
        
        if (coverInput.files[0]) {
            formData.append('cover_image', coverInput.files[0]);
        }
        
        // Envoyer la requête
        const response = await fetch('/api/playlists', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Erreur lors de la création de la playlist');
        }
        
        const data = await response.json();
        
        // Afficher une notification de succès
        showNotification('Playlist créée avec succès !', 'success');
        
        // Fermer la modal
        if (modal) {
            modal.style.display = 'none';
        }
        
        // Réinitialiser le formulaire
        form.reset();
        document.getElementById('coverPreview').style.backgroundImage = '';
        
        // Recharger la liste des playlists
        if (window.loadPlaylists) {
            window.loadPlaylists();
        }
        
    } catch (error) {
        console.error('Erreur lors de la création de la playlist:', error);
        showNotification('Erreur lors de la création de la playlist', 'error');
    }
}

// Ouvrir la modal d'édition
export function openEditModal(playlist) {
    const modal = document.getElementById('playlistModal');
    const nameInput = document.getElementById('playlistNameInput');
    const descInput = document.getElementById('playlistDescInput');
    const preview = document.getElementById('coverPreview');
    const modalTitle = document.getElementById('modalTitle');
    
    if (!modal || !nameInput || !descInput || !preview || !modalTitle) return;
    
    // Mettre à jour le titre
    modalTitle.textContent = 'Modifier la Playlist';
    
    // Remplir les champs
    nameInput.value = playlist.name || '';
    descInput.value = playlist.description || '';
    
    if (playlist.cover_image) {
        preview.style.backgroundImage = `url('${playlist.cover_image}')`;
    } else {
        preview.style.backgroundImage = '';
    }
    
    // Ajouter l'ID de la playlist au formulaire
    const form = document.getElementById('playlistForm');
    if (form) {
        form.dataset.playlistId = playlist.id;
    }
    
    // Afficher la modal
    modal.style.display = 'block';
}
