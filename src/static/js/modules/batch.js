// Module d'automatisation batch Citrus
// Permet de lancer des batchs de téléchargements (listes, scripts, playlists)

/**
 * Initialise le gestionnaire de téléchargements par lots
 */
// Importer les utilitaires DOM pour une gestion sécurisée des éléments
import { getElement, getElementValue, setElementText, setElementVisibility } from '/static/js/dom-utils.js';

export function initBatchDownloader() {
    const batchForm = getElement('batch-form');
    
    if (!batchForm) {
        console.log('Formulaire de batch non trouvé, module non initialisé');
        return;
    }
    
    batchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        try {
            let batchList = [];
            
            // Récupérer les URLs depuis le textarea de manière sécurisée
            const batchUrlsValue = getElementValue('batch-urls');
            if (batchUrlsValue) {
                batchList = parseBatchFile(batchUrlsValue);
            }
            
            // Récupérer les URLs depuis le fichier
            const batchFileInput = getElement('batch-file');
            if (batchFileInput && batchFileInput.files && batchFileInput.files.length > 0) {
                const file = batchFileInput.files[0];
                const content = await file.text();
                batchList = [...batchList, ...parseBatchFile(content)];
            }
            
            if (batchList.length === 0) {
                alert('Veuillez fournir au moins une URL');
                return;
            }
            
            // Afficher la progression de manière sécurisée
            const batchProgress = getElement('batch-progress');
            if (batchProgress) {
                batchProgress.style.display = 'block';
                batchProgress.value = 0;
                batchProgress.max = batchList.length;
            }
            
            // Démarrer le batch
            const result = await startBatch(batchList);
            
            // Mettre à jour le statut de manière sécurisée
            setElementText('batch-status', `Batch démarré: ${result.batchId}`);
            
            // Suivre la progression
            const interval = setInterval(async () => {
                try {
                    const status = await getBatchStatus(result.batchId);
                    
                    if (batchProgress) {
                        batchProgress.value = status.completed;
                    }
                    
                    setElementText('batch-status', `Progression: ${status.completed}/${status.total}`);
                    
                    if (status.completed === status.total) {
                        clearInterval(interval);
                        setElementText('batch-status', 'Batch terminé!');
                    }
                } catch (error) {
                    console.error('Erreur lors du suivi du batch:', error);
                    setElementText('batch-status', `Erreur: ${error.message}`);
                    clearInterval(interval);
                }
            }, 2000);
            
        } catch (error) {
            console.error('Erreur lors du démarrage du batch:', error);
            setElementText('batch-status', `Erreur: ${error.message}`);
        }
    });
}

export async function startBatch(batchList) {
    const resp = await fetch('/api/download/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ batch: batchList })
    });
    if (!resp.ok) throw new Error('Erreur lors du démarrage du batch');
    return await resp.json();
}

export async function getBatchStatus(batchId) {
    const resp = await fetch(`/api/download/batch/status/${batchId}`);
    if (!resp.ok) throw new Error('Erreur lors du suivi du batch');
    return await resp.json();
}

// Utilitaire pour parser des fichiers de batch (txt, csv, etc.)
export function parseBatchFile(fileContent) {
    return fileContent.split(/\r?\n/).filter(line => line.trim() !== '');
}

// TODO: Implement batch management logic for Citrus
