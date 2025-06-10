/**
 * Module de téléchargement multi-appareils pour Citrus Music Server
 * Permet le téléchargement de pistes individuelles ou par lots via plusieurs méthodes :
 * - Téléchargement direct
 * - Code QR pour appareils mobiles
 * - Envoi de lien par email
 */

import { getElement, getElementValue, setElementText, setElementVisibility, createElement, createModal, closeModal } from '/static/js/dom-utils.js';
import { showNotification } from '/static/js/notifications.js';

// Configuration du module
const CONFIG = {
    // Points d'accès API
    apiEndpoints: {
        trackInfo: '/api/tracks/',
        downloadToken: '/api/download-token',
        sendEmail: '/api/send-download-link',
        batchInfo: '/api/recent-tracks'
    },
    
    // IDs des modals
    modalIds: {
        downloadOptions: 'downloadOptionsModal',
        qrCode: 'qrCodeModal',
        email: 'emailModal',
        batchSelection: 'batchSelectionModal'
    },
    
    // Durée de validité des tokens (en minutes)
    tokenExpiryMinutes: 60,
    
    // Sélecteurs CSS
    selectors: {
        singleDownloadBtn: '.track-download-btn',
        shareBtn: '.track-share-btn',
        batchDownloadBtn: '#batchDownloadBtn'
    }
};

/**
 * Initialise le gestionnaire de téléchargement multi-appareils
 */
export function initMultiDeviceDownloader() {
    document.addEventListener('DOMContentLoaded', () => {
        // Éléments DOM
        const downloadButtons = document.querySelectorAll(CONFIG.selectors.singleDownloadBtn);
        const shareButtons = document.querySelectorAll(CONFIG.selectors.shareBtn);
        const batchDownloadBtn = document.querySelector(CONFIG.selectors.batchDownloadBtn);
        
        // Attacher les événements aux boutons de téléchargement individuels
        if (downloadButtons && downloadButtons.length > 0) {
            downloadButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const trackId = btn.dataset.trackId;
                    handleTrackDownload(trackId);
                });
            });
        }
        
        // Attacher les événements aux boutons de partage
        if (shareButtons && shareButtons.length > 0) {
            shareButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const trackId = btn.dataset.trackId;
                    handleTrackShare(trackId);
                });
            });
        }
        
        // Attacher l'événement au bouton de téléchargement par lots
        if (batchDownloadBtn) {
            batchDownloadBtn.addEventListener('click', (e) => {
                e.preventDefault();
                handleBatchDownload();
            });
        }
        
        // Initialiser le gestionnaire de partage
        initShareManager();
        
        console.log('Module de téléchargement multi-appareils initialisé');
    });
}

/**
 * Gère le téléchargement d'une piste individuelle
 * @param {string} trackId - ID de la piste à télécharger
 */
async function handleTrackDownload(trackId) {
    try {
        showNotification('Préparation du téléchargement...', 'info');
        
        // Récupérer les informations de la piste
        const response = await fetch(`${CONFIG.apiEndpoints.trackInfo}${trackId}`);
        
        if (!response.ok) {
            throw new Error('Impossible de récupérer les informations de la piste');
        }
        
        const trackInfo = await response.json();
        
        // Créer un token de téléchargement
        const tokenResponse = await fetch(CONFIG.apiEndpoints.downloadToken, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                track_ids: [trackId],
                expiry_minutes: CONFIG.tokenExpiryMinutes
            })
        });
        
        if (!tokenResponse.ok) {
            throw new Error('Impossible de créer un token de téléchargement');
        }
        
        const tokenData = await tokenResponse.json();
        
        // Afficher les options de téléchargement
        showDownloadOptions({
            type: 'single',
            track: trackInfo,
            token: tokenData.token,
            downloadUrl: tokenData.download_url
        });
        
    } catch (error) {
        console.error('Erreur lors du téléchargement:', error);
        showNotification(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Gère le partage d'une piste individuelle
 * @param {string} trackId - ID de la piste à partager
 */
async function handleTrackShare(trackId) {
    try {
        showNotification('Préparation du partage...', 'info');
        
        // Récupérer les informations de la piste
        const response = await fetch(`${CONFIG.apiEndpoints.trackInfo}${trackId}`);
        
        if (!response.ok) {
            throw new Error('Impossible de récupérer les informations de la piste');
        }
        
        const trackInfo = await response.json();
        
        // Créer un token de téléchargement
        const tokenResponse = await fetch(CONFIG.apiEndpoints.downloadToken, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                track_ids: [trackId],
                expiry_minutes: CONFIG.tokenExpiryMinutes
            })
        });
        
        if (!tokenResponse.ok) {
            throw new Error('Impossible de créer un token de téléchargement');
        }
        
        const tokenData = await tokenResponse.json();
        
        // Afficher les options de partage
        showQRCode({
            type: 'single',
            track: trackInfo,
            token: tokenData.token,
            downloadUrl: tokenData.download_url
        });
        
    } catch (error) {
        console.error('Erreur lors du partage:', error);
        showNotification(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Gère le téléchargement par lots
 */
async function handleBatchDownload() {
    try {
        // Afficher la modal de sélection des pistes
        showBatchSelectionModal();
    } catch (error) {
        console.error('Erreur lors du téléchargement par lots:', error);
        showNotification(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Affiche la modal de sélection des pistes pour le téléchargement par lots
 */
async function showBatchSelectionModal() {
    try {
        // Récupérer les pistes récentes
        const response = await fetch(CONFIG.apiEndpoints.batchInfo);
        
        if (!response.ok) {
            throw new Error('Impossible de récupérer les pistes');
        }
        
        const tracks = await response.json();
        
        // Créer le contenu de la modal
        const content = createElement('div', { className: 'batch-selection' }, [
            createElement('p', {}, 'Sélectionnez les pistes à télécharger en lot:'),
            createElement('div', { className: 'batch-actions' }, [
                createElement('button', { className: 'btn btn-sm', id: 'selectAllBtn' }, 'Sélectionner tout'),
                createElement('button', { className: 'btn btn-sm', id: 'deselectAllBtn' }, 'Désélectionner tout')
            ]),
            createElement('div', { className: 'track-list', id: 'batchTrackList' })
        ]);
        
        // Créer la modal
        const modal = createModal(
            CONFIG.modalIds.batchSelection,
            'Téléchargement par lots',
            content
        );
        
        // Ajouter les pistes à la liste
        const trackList = modal.querySelector('#batchTrackList');
        
        tracks.forEach(track => {
            const trackItem = createElement('div', { className: 'track-item' }, [
                createElement('input', { 
                    type: 'checkbox', 
                    className: 'track-checkbox',
                    id: `track-${track.id}`,
                    'data-track-id': track.id
                }),
                createElement('label', { htmlFor: `track-${track.id}` }, `${track.artist} - ${track.title}`)
            ]);
            
            trackList.appendChild(trackItem);
        });
        
        // Ajouter le bouton de téléchargement
        const downloadBtn = createElement('button', { 
            className: 'btn btn-primary', 
            id: 'confirmBatchDownloadBtn' 
        }, 'Télécharger la sélection');
        
        modal.querySelector('.modal-content').appendChild(downloadBtn);
        
        // Ajouter les événements
        modal.querySelector('#selectAllBtn').addEventListener('click', () => {
            modal.querySelectorAll('.track-checkbox').forEach(cb => cb.checked = true);
        });
        
        modal.querySelector('#deselectAllBtn').addEventListener('click', () => {
            modal.querySelectorAll('.track-checkbox').forEach(cb => cb.checked = false);
        });
        
        modal.querySelector('#confirmBatchDownloadBtn').addEventListener('click', async () => {
            // Récupérer les pistes sélectionnées
            const selectedTracks = [];
            modal.querySelectorAll('.track-checkbox:checked').forEach(cb => {
                selectedTracks.push(cb.dataset.trackId);
            });
            
            if (selectedTracks.length === 0) {
                showNotification('Veuillez sélectionner au moins une piste', 'warning');
                return;
            }
            
            // Fermer la modal de sélection
            closeModal(CONFIG.modalIds.batchSelection);
            
            // Créer un token de téléchargement pour les pistes sélectionnées
            await processBatchDownload(selectedTracks);
        });
        
    } catch (error) {
        console.error('Erreur lors de l\'affichage de la modal de sélection:', error);
        showNotification(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Traite le téléchargement par lots
 * @param {Array<string>} trackIds - IDs des pistes à télécharger
 */
async function processBatchDownload(trackIds) {
    try {
        showNotification(`Préparation du téléchargement de ${trackIds.length} pistes...`, 'info');
        
        // Créer un token de téléchargement
        const tokenResponse = await fetch(CONFIG.apiEndpoints.downloadToken, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                track_ids: trackIds,
                expiry_minutes: CONFIG.tokenExpiryMinutes,
                batch: true
            })
        });
        
        if (!tokenResponse.ok) {
            throw new Error('Impossible de créer un token de téléchargement');
        }
        
        const tokenData = await tokenResponse.json();
        
        // Afficher les options de téléchargement
        showDownloadOptions({
            type: 'batch',
            trackCount: trackIds.length,
            token: tokenData.token,
            downloadUrl: tokenData.download_url
        });
        
    } catch (error) {
        console.error('Erreur lors du téléchargement par lots:', error);
        showNotification(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Affiche les options de téléchargement dans une modal
 * @param {Object} downloadInfo - Informations sur le téléchargement
 */
function showDownloadOptions(downloadInfo) {
    // Créer le contenu de la modal
    const content = createElement('div', {}, [
        // Informations sur le téléchargement
        createElement('div', { className: 'download-info' }, [
            downloadInfo.type === 'single' 
                ? createElement('div', { className: 'track-info' }, [
                    createElement('h3', {}, downloadInfo.track.title),
                    createElement('p', {}, `Artiste: ${downloadInfo.track.artist}`),
                    createElement('p', {}, `Album: ${downloadInfo.track.album || 'Non spécifié'}`)
                ])
                : createElement('div', { className: 'batch-info' }, [
                    createElement('h3', {}, 'Téléchargement par lots'),
                    createElement('p', {}, `${downloadInfo.trackCount} pistes sélectionnées`)
                ])
        ]),
        
        // Options de téléchargement
        createElement('h4', {}, 'Comment souhaitez-vous télécharger ?'),
        createElement('div', { className: 'download-options' }, [
            // Option 1: Téléchargement direct
            createElement('div', { 
                className: 'option-card', 
                id: 'directDownloadOption'
            }, [
                createElement('i', { className: 'fas fa-download' }),
                createElement('h4', {}, 'Téléchargement direct'),
                createElement('p', {}, 'Télécharger sur cet appareil')
            ]),
            
            // Option 2: QR Code
            createElement('div', { 
                className: 'option-card', 
                id: 'qrCodeOption'
            }, [
                createElement('i', { className: 'fas fa-qrcode' }),
                createElement('h4', {}, 'Code QR'),
                createElement('p', {}, 'Scanner avec un appareil mobile')
            ]),
            
            // Option 3: Email
            createElement('div', { 
                className: 'option-card', 
                id: 'emailOption'
            }, [
                createElement('i', { className: 'fas fa-envelope' }),
                createElement('h4', {}, 'Envoyer par email'),
                createElement('p', {}, 'Recevoir un lien par email')
            ])
        ])
    ]);
    
    // Créer la modal
    const modal = createModal(
        CONFIG.modalIds.downloadOptions,
        'Options de téléchargement',
        content
    );
    
    // Ajouter les événements
    modal.querySelector('#directDownloadOption').addEventListener('click', () => {
        closeModal(CONFIG.modalIds.downloadOptions);
        startDirectDownload(downloadInfo);
    });
    
    modal.querySelector('#qrCodeOption').addEventListener('click', () => {
        closeModal(CONFIG.modalIds.downloadOptions);
        showQRCode(downloadInfo);
    });
    
    modal.querySelector('#emailOption').addEventListener('click', () => {
        closeModal(CONFIG.modalIds.downloadOptions);
        showEmailForm(downloadInfo);
    });
}

/**
 * Démarre le téléchargement direct sur l'appareil actuel
 * @param {Object} downloadInfo - Informations sur le téléchargement
 */
function startDirectDownload(downloadInfo) {
    try {
        showNotification('Démarrage du téléchargement...', 'info');
        
        // Créer un lien de téléchargement invisible
        const downloadLink = document.createElement('a');
        downloadLink.href = downloadInfo.downloadUrl;
        downloadLink.download = downloadInfo.type === 'single' 
            ? `${downloadInfo.track.artist} - ${downloadInfo.track.title}.mp3`
            : 'citrus_music_selection.zip';
        
        // Ajouter le lien au document et cliquer dessus
        document.body.appendChild(downloadLink);
        downloadLink.click();
        
        // Supprimer le lien après un court délai
        setTimeout(() => {
            document.body.removeChild(downloadLink);
            showNotification('Téléchargement lancé avec succès !', 'success');
        }, 100);
        
    } catch (error) {
        console.error('Erreur lors du téléchargement direct:', error);
        showNotification(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Affiche un code QR pour télécharger sur un appareil mobile
 * @param {Object} downloadInfo - Informations sur le téléchargement
 */
function showQRCode(downloadInfo) {
    try {
        // Créer le contenu de la modal
        const content = createElement('div', {}, [
            createElement('p', {}, 'Scannez ce code QR avec votre appareil mobile pour télécharger:'),
            createElement('div', { className: 'qr-code-wrapper' }, [
                createElement('div', { id: 'qrCode' }),
                createElement('p', {}, downloadInfo.type === 'single' 
                    ? `${downloadInfo.track.artist} - ${downloadInfo.track.title}`
                    : `${downloadInfo.trackCount} pistes sélectionnées`
                )
            ]),
            createElement('div', { className: 'qr-fallback' }, [
                createElement('p', {}, 'Si vous ne pouvez pas scanner le code QR, utilisez ce lien:'),
                createElement('a', { 
                    href: downloadInfo.downloadUrl,
                    target: '_blank'
                }, downloadInfo.downloadUrl)
            ])
        ]);
        
        // Créer la modal
        const modal = createModal(
            CONFIG.modalIds.qrCode,
            'Téléchargement mobile',
            content
        );
        
        // Générer le code QR
        if (window.QRCode) {
            new QRCode(document.getElementById('qrCode'), {
                text: downloadInfo.downloadUrl,
                width: 200,
                height: 200,
                colorDark: '#000000',
                colorLight: '#ffffff',
                correctLevel: QRCode.CorrectLevel.H
            });
        } else {
            document.getElementById('qrCode').innerHTML = 
                '<p>Impossible de générer le code QR. Utilisez le lien ci-dessous.</p>';
        }
        
    } catch (error) {
        console.error('Erreur lors de l\'affichage du code QR:', error);
        showNotification(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Affiche le formulaire d'envoi par email
 * @param {Object} downloadInfo - Informations sur le téléchargement
 */
function showEmailForm(downloadInfo) {
    try {
        // Créer le contenu de la modal
        const content = createElement('div', {}, [
            createElement('p', {}, 'Entrez votre adresse email pour recevoir le lien de téléchargement:'),
            createElement('form', { id: 'emailForm', className: 'glass-form' }, [
                createElement('div', { className: 'form-group' }, [
                    createElement('i', { className: 'fas fa-envelope input-icon' }),
                    createElement('input', { 
                        type: 'email', 
                        id: 'emailInput', 
                        className: 'form-input',
                        placeholder: 'Votre adresse email',
                        required: true
                    })
                ]),
                createElement('button', { 
                    type: 'submit', 
                    className: 'btn btn-primary'
                }, 'Envoyer')
            ])
        ]);
        
        // Créer la modal
        const modal = createModal(
            CONFIG.modalIds.email,
            'Envoi par email',
            content
        );
        
        // Ajouter l'événement de soumission du formulaire
        modal.querySelector('#emailForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = getElementValue('emailInput');
            
            if (!email) {
                showNotification('Veuillez entrer une adresse email valide', 'warning');
                return;
            }
            
            closeModal(CONFIG.modalIds.email);
            await sendDownloadLink(email, downloadInfo);
        });
        
    } catch (error) {
        console.error('Erreur lors de l\'affichage du formulaire d\'email:', error);
        showNotification(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Envoie un lien de téléchargement par email
 * @param {string} email - Adresse email du destinataire
 * @param {Object} downloadInfo - Informations sur le téléchargement
 */
async function sendDownloadLink(email, downloadInfo) {
    try {
        showNotification('Envoi du lien par email...', 'info');
        
        // Envoyer la requête au serveur
        const response = await fetch(CONFIG.apiEndpoints.sendEmail, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                token: downloadInfo.token,
                type: downloadInfo.type,
                track_info: downloadInfo.type === 'single' ? downloadInfo.track : null,
                track_count: downloadInfo.type === 'batch' ? downloadInfo.trackCount : null
            })
        });
        
        if (!response.ok) {
            throw new Error('Impossible d\'envoyer l\'email');
        }
        
        showNotification('Lien de téléchargement envoyé avec succès !', 'success');
        
    } catch (error) {
        console.error('Erreur lors de l\'envoi de l\'email:', error);
        showNotification(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Initialise le gestionnaire de partage pour les appareils mobiles
 */
function initShareManager() {
    // Vérifier si l'API Web Share est disponible
    if (navigator.share) {
        // Ajouter des boutons de partage natifs pour les appareils mobiles
        document.querySelectorAll('.track-share-btn').forEach(btn => {
            btn.style.display = 'inline-block';
            
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const trackId = btn.dataset.trackId;
                const trackElement = btn.closest('.track-card');
                
                if (!trackElement) return;
                
                const trackTitle = trackElement.querySelector('.track-title')?.textContent || 'Piste musicale';
                const trackArtist = trackElement.querySelector('.track-artist')?.textContent || 'Artiste inconnu';
                
                try {
                    await navigator.share({
                        title: `${trackArtist} - ${trackTitle}`,
                        text: `Écoute "${trackTitle}" par ${trackArtist} sur Citrus Music Server`,
                        url: window.location.origin + `/track/${trackId}`
                    });
                    
                    showNotification('Partage réussi !', 'success');
                } catch (error) {
                    if (error.name !== 'AbortError') {
                        console.error('Erreur lors du partage:', error);
                        showNotification('Erreur lors du partage', 'error');
                    }
                }
            });
        });
    }
}

/**
 * Démarre le téléchargement direct sur l'appareil actuel
 * @param {Object} downloadInfo - Informations sur le téléchargement
 */
async function startDirectDownload(downloadInfo) {
    try {
        showNotification('Démarrage du téléchargement...', 'info');
        
        let endpoint, data;
        
        if (downloadInfo.type === 'single') {
            endpoint = `/api/tracks/${downloadInfo.id}/download`;
            data = { format: 'mp3' };
        } else {
            endpoint = '/api/tracks/batch-download';
            data = { 
                track_ids: downloadInfo.ids,
                format: 'zip'
            };
        }
        
        // Créer un lien temporaire pour le téléchargement
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error('Erreur lors de la préparation du téléchargement');
        
        const result = await response.json();
        
        // Créer un lien de téléchargement et cliquer dessus
        const downloadLink = document.createElement('a');
        downloadLink.href = result.download_url;
        downloadLink.download = result.filename || 'citrus_music.mp3';
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
        
        // Fermer la modal
        const modal = getElement('downloadOptionsModal');
        if (modal) modal.style.display = 'none';
        
        showNotification('Téléchargement démarré!', 'success');
        
    } catch (error) {
        console.error('Erreur de téléchargement direct:', error);
        showNotification(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Affiche un code QR pour télécharger sur un appareil mobile
 * @param {Object} downloadInfo - Informations sur le téléchargement
 */
async function showQRCode(downloadInfo) {
    try {
        const qrCodeContainer = getElement('qrCodeContainer');
        const qrCodeElement = getElement('qrCode');
        
        if (!qrCodeContainer || !qrCodeElement) return;
        
        // Masquer les autres options
        const emailForm = getElement('emailForm');
        if (emailForm) emailForm.style.display = 'none';
        
        // Afficher le conteneur de QR code
        qrCodeContainer.style.display = 'block';
        
        // Générer un token temporaire pour ce téléchargement
        const response = await fetch('/api/download-token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: downloadInfo.type,
                id: downloadInfo.type === 'single' ? downloadInfo.id : null,
                ids: downloadInfo.type === 'batch' ? downloadInfo.ids : null
            })
        });
        
        if (!response.ok) throw new Error('Erreur lors de la génération du token');
        
        const result = await response.json();
        
        // Construire l'URL de téléchargement
        const downloadUrl = `${window.location.origin}/download/${result.token}`;
        
        // Générer le code QR (utilise une bibliothèque QR code)
        if (window.QRCode) {
            qrCodeElement.innerHTML = '';
            new QRCode(qrCodeElement, {
                text: downloadUrl,
                width: 200,
                height: 200
            });
        } else {
            // Fallback si la bibliothèque QR n'est pas chargée
            qrCodeElement.innerHTML = `
                <div class="qr-fallback">
                    <p>URL de téléchargement:</p>
                    <a href="${downloadUrl}" target="_blank">${downloadUrl}</a>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Erreur de génération de QR code:', error);
        showNotification(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Affiche le formulaire d'envoi par email
 */
function showEmailForm() {
    const emailForm = getElement('emailForm');
    const qrCodeContainer = getElement('qrCodeContainer');
    
    if (!emailForm) return;
    
    // Masquer le QR code s'il est affiché
    if (qrCodeContainer) qrCodeContainer.style.display = 'none';
    
    // Afficher le formulaire d'email
    emailForm.style.display = 'block';
}

/**
 * Envoie un lien de téléchargement par email
 * @param {string} email - Adresse email du destinataire
 * @param {Object} downloadInfo - Informations sur le téléchargement
 */
async function sendDownloadLink(email, downloadInfo) {
    try {
        if (!email) {
            showNotification('Veuillez entrer une adresse email valide', 'warning');
            return;
        }
        
        showNotification('Envoi du lien par email...', 'info');
        
        const response = await fetch('/api/send-download-link', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                type: downloadInfo.type,
                id: downloadInfo.type === 'single' ? downloadInfo.id : null,
                ids: downloadInfo.type === 'batch' ? downloadInfo.ids : null
            })
        });
        
        if (!response.ok) throw new Error('Erreur lors de l\'envoi de l\'email');
        
        // Fermer la modal
        const modal = getElement('downloadOptionsModal');
        if (modal) modal.style.display = 'none';
        
        showNotification('Lien de téléchargement envoyé par email!', 'success');
        
    } catch (error) {
        console.error('Erreur d\'envoi d\'email:', error);
        showNotification(`Erreur: ${error.message}`, 'error');
    }
}

/**
 * Initialise le gestionnaire de partage pour les appareils mobiles
 */
function initShareManager() {
    // Vérifier si l'API Web Share est disponible (principalement sur mobile)
    if (navigator.share) {
        // Ajouter des boutons de partage aux éléments qui peuvent être partagés
        document.querySelectorAll('.track-share-btn').forEach(btn => {
            btn.style.display = 'inline-flex';
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                
                const trackId = btn.dataset.trackId;
                const trackTitle = btn.dataset.title || 'Musique';
                const trackArtist = btn.dataset.artist || 'Artiste';
                
                try {
                    await navigator.share({
                        title: `${trackTitle} - ${trackArtist}`,
                        text: `Écoute "${trackTitle}" par ${trackArtist} sur Citrus Music Server!`,
                        url: `${window.location.origin}/tracks/${trackId}`
                    });
                } catch (error) {
                    console.log('Partage annulé ou erreur', error);
                }
            });
        });
    }
}
