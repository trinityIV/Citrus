/**
 * Module Player - Gestion du lecteur audio
 */

import { showNotification } from './notifications.js';

// Variables globales du lecteur
let audio;
let currentTrackIndex = 0;
let tracks = [];
let isShuffled = false;
let originalTracks = [];
let repeatMode = 'none'; // 'none', 'all', 'one'

// Initialisation du lecteur audio
export function initPlayer(config) {
    // Créer l'élément audio
    audio = new Audio();
    
    // Récupérer les éléments du DOM
    const playPauseBtn = document.getElementById('playPauseBtn');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const progressBar = document.getElementById('progress');
    const progressContainer = document.getElementById('progressBar');
    const currentTimeEl = document.getElementById('currentTime');
    const durationEl = document.getElementById('duration');
    const volumeControl = document.getElementById('volume');
    const shuffleBtn = document.getElementById('shuffleBtn');
    const repeatBtn = document.getElementById('repeatBtn');
    
    // Charger les pistes depuis l'API
    loadTracks(config);
    
    // Événements du lecteur audio
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', togglePlayPause);
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', playPrevious);
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', playNext);
    }
    
    if (progressContainer) {
        progressContainer.addEventListener('click', (e) => {
            const width = progressContainer.clientWidth;
            const clickX = e.offsetX;
            const duration = audio.duration;
            audio.currentTime = (clickX / width) * duration;
        });
    }
    
    if (volumeControl) {
        // Définir le volume initial
        const savedVolume = localStorage.getItem('volume') || 0.8;
        audio.volume = savedVolume;
        volumeControl.value = savedVolume;
        
        volumeControl.addEventListener('input', (e) => {
            const volume = e.target.value;
            audio.volume = volume;
            localStorage.setItem('volume', volume);
        });
    }
    
    if (shuffleBtn) {
        shuffleBtn.addEventListener('click', toggleShuffle);
    }
    
    if (repeatBtn) {
        repeatBtn.addEventListener('click', toggleRepeat);
    }
    
    // Événements audio
    audio.addEventListener('play', () => {
        if (playPauseBtn) {
            playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        }
    });
    
    audio.addEventListener('pause', () => {
        if (playPauseBtn) {
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    });
    
    audio.addEventListener('timeupdate', () => {
        updateProgress(progressBar, currentTimeEl, durationEl);
    });
    
    audio.addEventListener('ended', () => {
        handleTrackEnd();
    });
    
    // Mettre à jour l'heure actuelle toutes les secondes
    setInterval(() => {
        updateCurrentTime(currentTimeEl);
    }, 1000);
    
    // Exposer les fonctions globales
    window.playTrack = playTrackByData;
}

// Charger les pistes depuis l'API
async function loadTracks(config) {
    try {
        const response = await fetch(config.apiEndpoints.library);
        const data = await response.json();
        tracks = data;
        originalTracks = [...data];
        
        if (tracks.length > 0) {
            updatePlayerInfo(tracks[0]);
        }
    } catch (error) {
        console.error('Erreur lors du chargement des pistes:', error);
    }
}

// Mettre à jour les informations du lecteur
function updatePlayerInfo(track) {
    const playerTitle = document.getElementById('playerTitle');
    const playerArtist = document.getElementById('playerArtist');
    const playerCover = document.getElementById('playerCover');
    
    if (playerTitle) {
        playerTitle.textContent = track.title || 'Titre inconnu';
    }
    
    if (playerArtist) {
        playerArtist.textContent = track.artist || 'Artiste inconnu';
    }
    
    if (playerCover) {
        if (track.cover_art) {
            playerCover.style.backgroundImage = `url('${track.cover_art}')`;
            playerCover.innerHTML = '';
        } else {
            playerCover.style.backgroundImage = 'none';
            playerCover.innerHTML = '<i class="fas fa-music"></i>';
        }
    }
}

// Mettre à jour la barre de progression
function updateProgress(progressBar, currentTimeEl, durationEl) {
    if (!progressBar) return;
    
    const duration = audio.duration;
    const currentTime = audio.currentTime;
    
    if (isNaN(duration)) return;
    
    const progressPercent = (currentTime / duration) * 100;
    progressBar.style.width = `${progressPercent}%`;
    
    // Mettre à jour l'affichage du temps
    if (currentTimeEl) {
        currentTimeEl.textContent = formatTime(currentTime);
    }
    
    if (durationEl) {
        durationEl.textContent = formatTime(duration);
    }
}

// Mettre à jour le temps actuel
function updateCurrentTime(currentTimeEl) {
    if (!currentTimeEl || isNaN(audio.duration)) return;
    
    currentTimeEl.textContent = formatTime(audio.currentTime);
}

// Formater le temps (secondes en MM:SS)
function formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    
    return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
}

// Lecture/Pause
function togglePlayPause() {
    if (audio.paused) {
        audio.play().catch(error => {
            console.error('Erreur lors de la lecture:', error);
            showNotification('Impossible de lire la piste', 'error');
        });
    } else {
        audio.pause();
    }
}

// Piste précédente
function playPrevious() {
    if (tracks.length === 0) return;
    
    if (audio.currentTime > 3) {
        // Si la lecture est > 3 secondes, revenir au début de la piste
        audio.currentTime = 0;
    } else {
        // Sinon, passer à la piste précédente
        currentTrackIndex = (currentTrackIndex - 1 + tracks.length) % tracks.length;
        playTrack(currentTrackIndex);
    }
}

// Piste suivante
function playNext() {
    if (tracks.length === 0) return;
    
    currentTrackIndex = (currentTrackIndex + 1) % tracks.length;
    playTrack(currentTrackIndex);
}

// Jouer une piste par index
function playTrack(index) {
    if (index < 0 || index >= tracks.length) return;
    
    currentTrackIndex = index;
    const track = tracks[index];
    
    updatePlayerInfo(track);
    
    // Mettre à jour la source audio
    if (audio.src !== track.path) {
        audio.src = track.path;
        audio.load();
    }
    
    // Lire la piste
    audio.play().catch(error => {
        console.error('Erreur lors de la lecture:', error);
        showNotification('Impossible de lire la piste', 'error');
    });
}

// Jouer une piste par données
function playTrackByData(track) {
    // Trouver l'index de la piste dans la liste
    const index = tracks.findIndex(t => t.path === track.path);
    
    if (index !== -1) {
        playTrack(index);
    } else {
        // Si la piste n'est pas dans la liste, la jouer directement
        updatePlayerInfo(track);
        
        // Mettre à jour la source audio
        if (audio.src !== track.path) {
            audio.src = track.path;
            audio.load();
        }
        
        // Lire la piste
        audio.play().catch(error => {
            console.error('Erreur lors de la lecture:', error);
            showNotification('Impossible de lire la piste', 'error');
        });
    }
}

// Gérer la fin d'une piste
function handleTrackEnd() {
    if (repeatMode === 'one') {
        // Répéter la piste actuelle
        audio.currentTime = 0;
        audio.play().catch(error => {
            console.error('Erreur lors de la lecture:', error);
        });
    } else if (repeatMode === 'all' || currentTrackIndex < tracks.length - 1) {
        // Passer à la piste suivante
        playNext();
    } else {
        // Fin de la playlist
        currentTrackIndex = 0;
        updatePlayerInfo(tracks[0]);
        audio.pause();
    }
}

// Activer/désactiver la lecture aléatoire
function toggleShuffle() {
    const shuffleBtn = document.getElementById('shuffleBtn');
    
    isShuffled = !isShuffled;
    
    if (isShuffled) {
        // Sauvegarder l'ordre original
        originalTracks = [...tracks];
        
        // Mélanger les pistes
        tracks = shuffleArray([...tracks]);
        
        // Trouver la piste actuelle dans le nouveau tableau
        const currentTrack = originalTracks[currentTrackIndex];
        currentTrackIndex = tracks.findIndex(track => track.path === currentTrack.path);
        
        if (shuffleBtn) {
            shuffleBtn.classList.add('active');
        }
    } else {
        // Restaurer l'ordre original
        const currentTrack = tracks[currentTrackIndex];
        tracks = [...originalTracks];
        currentTrackIndex = tracks.findIndex(track => track.path === currentTrack.path);
        
        if (shuffleBtn) {
            shuffleBtn.classList.remove('active');
        }
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

// Changer le mode de répétition
function toggleRepeat() {
    const repeatBtn = document.getElementById('repeatBtn');
    
    if (repeatMode === 'none') {
        repeatMode = 'all';
        if (repeatBtn) {
            repeatBtn.innerHTML = '<i class="fas fa-repeat"></i>';
            repeatBtn.classList.add('active');
        }
    } else if (repeatMode === 'all') {
        repeatMode = 'one';
        if (repeatBtn) {
            repeatBtn.innerHTML = '<i class="fas fa-repeat-1"></i>';
            repeatBtn.classList.add('active');
        }
    } else {
        repeatMode = 'none';
        if (repeatBtn) {
            repeatBtn.innerHTML = '<i class="fas fa-repeat"></i>';
            repeatBtn.classList.remove('active');
        }
    }
}
