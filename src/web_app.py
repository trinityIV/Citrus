import os
import sys
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
import subprocess
import tempfile
import os
import random
from flask_login import LoginManager, UserMixin, current_user, AnonymousUserMixin, login_required, login_user, logout_user
from src.config.logging_config import setup_logging
from werkzeug.utils import secure_filename
import yt_dlp
from dotenv import load_dotenv
import spotipy

from src.services.downloader import DownloadManager
from src.services.metadata import MetadataExtractor



# Configuration du logger
logger = setup_logging()

# Chargement des variables d'environnement
load_dotenv()

# Configuration de l'application
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-me')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Enregistrement des blueprints
# TODO: Réactiver une fois les clés Spotify configurées
# from spotify import spotify
# app.register_blueprint(spotify)

# Configuration de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    from src.models.user import User
    return User.query.get(int(user_id))

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

# --- STREAM MAGNET/TORRENT ENDPOINT ---
from flask import Response
@app.route('/api/stream/magnet', methods=['POST'])
def stream_magnet():
    if request.content_type and request.content_type.startswith('application/json'):
        data = request.get_json()
        magnet = data.get('magnet')
        temp_torrent = None
    elif 'torrent' in request.files:
        file = request.files['torrent']
        temp_dir = tempfile.mkdtemp()
        temp_torrent = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(temp_torrent)
        magnet = None
    else:
        return jsonify({'error': 'Aucun lien magnet ou fichier torrent fourni.'}), 400
    port = random.randint(40000, 49999)
    if magnet:
        cmd = f"peerflix '{magnet}' --port {port} --list --path /tmp --no-quit --on-error exit"
    elif temp_torrent:
        cmd = f"peerflix '{temp_torrent}' --port {port} --list --path /tmp --no-quit --on-error exit"
    else:
        return jsonify({'error': 'Aucun lien magnet ou fichier torrent fourni.'}), 400
    subprocess.Popen(cmd, shell=True)
    stream_url = f"http://localhost:{port}"
    return jsonify({'stream_url': stream_url})

# --- PAGE IPTV ---
@app.route('/iptv')
def iptv_page():
    return render_template('iptv.html')

# --- PAGE STREAM ---
@app.route('/stream')
def stream_page():
    return render_template('stream.html')


# Configuration de Spotify
sp = None



# Routes d'authentification
@app.route('/login', methods=['GET', 'POST'])
def login():
    from models.user import User
    from database import db
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            error = "Nom d'utilisateur ou mot de passe incorrect."
        else:
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    from models.user import User
    from database import db
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            error = 'Veuillez remplir tous les champs.'
        elif User.query.filter_by(username=username).first():
            error = 'Nom d\'utilisateur déjà pris.'
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
    return render_template('register.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

from flask_login import login_required

@app.before_request
def require_login():
    allowed_routes = {'login', 'register', 'static'}
    if not current_user.is_authenticated and request.endpoint and not any(request.endpoint.startswith(r) for r in allowed_routes):
        return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Page d'accueil"""
    # Calcul des statistiques
    stats = {
        'tracks': len(list(MUSIC_FOLDER.glob('*.*'))),
        'downloads': len(download_manager.tasks) if hasattr(download_manager, 'tasks') else 0,
        'playlists': 0  # À implémenter plus tard
    }
    return render_template('index.html', stats=stats)

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
    # Démarrer le serveur sur toutes les interfaces en mode release
    app.run(host='0.0.0.0', port=5000, debug=False)
