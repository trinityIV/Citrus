from flask import Blueprint, jsonify, request
from ..services.search import search_tracks
from ..services.playlist import get_playlist_info
from ..services.download import start_batch_download
from ..utils.spotify import get_spotify_client
from ..utils.exceptions import ServiceError

api = Blueprint('api', __name__)

@api.route('/search')
def search():
    """
    Recherche de musique à travers différents services
    """
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
        
    try:
        # Recherche sur tous les services disponibles
        results = search_tracks(query)
        return jsonify(results)
    except ServiceError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred'}), 500

@api.route('/playlist/info', methods=['POST'])
def playlist_info():
    """
    Récupère les informations d'une playlist
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
        
    try:
        # Récupérer les infos de la playlist
        playlist = get_playlist_info(data['url'])
        return jsonify(playlist)
    except ServiceError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred'}), 500

@api.route('/downloads/batch', methods=['POST'])
def batch_download():
    """
    Démarre un téléchargement en masse
    """
    data = request.get_json()
    if not data or 'tracks' not in data:
        return jsonify({'error': 'Tracks list is required'}), 400
        
    try:
        # Démarrer les téléchargements
        result = start_batch_download(data['tracks'])
        return jsonify(result)
    except ServiceError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred'}), 500

@api.route('/spotify/search')
def spotify_search():
    """
    Recherche spécifiquement sur Spotify
    """
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
        
    try:
        spotify = get_spotify_client()
        results = spotify.search(query)
        return jsonify(results)
    except ServiceError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred'}), 500

@api.route('/spotify/playlist/<playlist_id>')
def spotify_playlist(playlist_id):
    """
    Récupère une playlist Spotify spécifique
    """
    try:
        spotify = get_spotify_client()
        playlist = spotify.get_playlist(playlist_id)
        return jsonify(playlist)
    except ServiceError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred'}), 500
