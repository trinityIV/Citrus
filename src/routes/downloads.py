"""
Routes pour le téléchargement de fichiers audio
"""

from flask import Blueprint, send_file, request, jsonify
from ..utils.auth import login_required
from ..models.track import Track
import os

downloads_bp = Blueprint('downloads', __name__)

@downloads_bp.route('/download/<int:track_id>')
@login_required
def download_track(track_id):
    """
    Télécharge une piste audio dans le format spécifié
    Format supportés : mp3, wav, ogg, flac
    """
    # Récupérer le format demandé (mp3 par défaut)
    format = request.args.get('format', 'mp3').lower()
    
    # Vérifier que le format est supporté
    if format not in ['mp3', 'wav', 'ogg', 'flac']:
        return jsonify({'error': 'Format non supporté'}), 400
    
    # Récupérer la piste
    track = Track.query.get_or_404(track_id)
    
    # Chemin du fichier
    file_path = track.file_path
    
    # Envoyer le fichier avec le bon nom et type MIME
    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"{track.title}.{format}",
        mimetype=f"audio/{format}"
    )

@downloads_bp.route('/download/playlist/<int:playlist_id>')
@login_required
def download_playlist(playlist_id):
    """
    Télécharge toute une playlist au format ZIP
    Chaque fichier sera dans le format spécifié
    """
    # TODO: Implémenter le téléchargement de playlist
    # - Créer un fichier ZIP temporaire
    # - Ajouter chaque piste dans le format demandé
    # - Envoyer le ZIP
    pass
