"""
Routes pour le téléchargement de musique
"""

from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
from pathlib import Path
from ..services.downloader import DownloadManager

download_bp = Blueprint('download', __name__)

# Initialiser le gestionnaire de téléchargements
download_manager = None

def init_download_manager(app):
    """Initialise le gestionnaire de téléchargements"""
    global download_manager
    if not download_manager:
        with app.app_context():
            download_dir = Path(current_app.config['UPLOAD_FOLDER']) / 'downloads'
            download_dir.mkdir(parents=True, exist_ok=True)
            download_manager = DownloadManager(download_dir)

# Initialisation au démarrage
from flask import current_app
if current_app:
    init_download_manager(current_app._get_current_object())

@download_bp.route('/api/downloads', methods=['POST'])
@login_required
def start_download():
    """Démarre un nouveau téléchargement"""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL requise'}), 400
    
    url = data['url']
    service = data.get('service', 'youtube')  # Par défaut YouTube
    
    try:
        task_id = download_manager.add_download(url, service)
        return jsonify({
            'task_id': task_id,
            'message': 'Téléchargement démarré'
        }), 202
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@download_bp.route('/api/downloads/<task_id>', methods=['GET'])
@login_required
def get_download_status(task_id):
    """Récupère le statut d'un téléchargement"""
    task = download_manager.get_task(task_id)
    
    if not task:
        return jsonify({
            'error': 'Tâche non trouvée'
        }), 404
    
    return jsonify(task.to_dict())

@download_bp.route('/api/downloads/<task_id>', methods=['DELETE'])
@login_required
def cancel_download(task_id):
    """Annule un téléchargement"""
    success = download_manager.cancel_task(task_id)
    
    if not success:
        return jsonify({
            'error': 'Impossible d\'annuler la tâche'
        }), 404
    
    return jsonify({
        'message': 'Téléchargement annulé'
    })

@download_bp.route('/api/downloads', methods=['GET'])
@login_required
def list_downloads():
    """Liste tous les téléchargements"""
    tasks = download_manager.get_all_tasks()
    return jsonify({
        'downloads': tasks  # Les tâches sont déjà des dictionnaires
    })
