import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import yt_dlp
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from services.downloader import DownloadManager
from services.metadata import MetadataExtractor

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('citrus.log')
    ]
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()

# Configuration de l'application
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-me')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Chemins importants
BASE_DIR = Path(__file__).parent.absolute()
UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
MUSIC_FOLDER = BASE_DIR / 'static' / 'music'

# Création des dossiers nécessaires
for folder in [UPLOAD_FOLDER, MUSIC_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

# Initialisation des services
download_manager = DownloadManager(MUSIC_FOLDER)
metadata_extractor = MetadataExtractor()

# Configuration de Spotify
sp = None
if os.getenv('SPOTIFY_CLIENT_ID') and os.getenv('SPOTIFY_CLIENT_SECRET'):
    auth_manager = SpotifyClientCredentials(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def download():
    """API pour démarrer un téléchargement"""
    try:
        data = request.get_json()
        url = data.get('url')
        service = data.get('service', 'youtube')
        
        if not url:
            return jsonify({'error': 'URL manquante'}), 400
            
        # Démarrer le téléchargement
        task_id = download_manager.add_download(url, service)
        return jsonify({
            'status': 'started',
            'task_id': task_id
        })
        
    except Exception as e:
        logger.error(f'Erreur lors du téléchargement: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<task_id>')
def status(task_id):
    """API pour vérifier l'état d'un téléchargement"""
    task = download_manager.get_status(task_id)
    if not task:
        return jsonify({'error': 'Tâche non trouvée'}), 404
    return jsonify(task)

@app.route('/api/library')
def library():
    """API pour obtenir la bibliothèque musicale"""
    try:
        tracks = []
        for file in MUSIC_FOLDER.glob('*.*'):
            if file.suffix.lower() in ['.mp3', '.wav', '.ogg', '.m4a']:
                tracks.append({
                    'id': file.stem,
                    'filename': file.name,
                    'path': f'/static/music/{file.name}',
                    'metadata': metadata_extractor.extract(file)
                })
        return jsonify(tracks)
    except Exception as e:
        logger.error(f'Erreur lors de la lecture de la bibliothèque: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/spotify/search')
def search_spotify():
    """API pour rechercher des titres sur Spotify"""
    if not sp:
        return jsonify({'error': 'Spotify non configuré'}), 501
        
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Requête de recherche manquante'}), 400
        
    try:
        results = sp.search(q=query, limit=10, type='track')
        return jsonify([{
            'id': item['id'],
            'title': item['name'],
            'artist': ', '.join([a['name'] for a in item['artists']]),
            'album': item['album']['name'],
            'cover': item['album']['images'][0]['url'] if item['album']['images'] else None
        } for item in results['tracks']['items']])
    except Exception as e:
        logger.error(f'Erreur lors de la recherche Spotify: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Gestion des erreurs
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Ressource non trouvée'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f'Erreur serveur: {str(error)}')
    return jsonify({'error': 'Erreur interne du serveur'}), 500

if __name__ == '__main__':
    # Démarrer le serveur sur toutes les interfaces
    app.run(host='0.0.0.0', port=5000, debug=True)
