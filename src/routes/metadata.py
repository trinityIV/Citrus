"""
Routes pour la gestion des métadonnées et des playlists
"""

from flask import Blueprint, jsonify, request
from ..utils.auth import login_required
from ..utils.metadata_manager import metadata_manager
from werkzeug.utils import secure_filename
import os
from pathlib import Path

metadata_bp = Blueprint('metadata', __name__)

@metadata_bp.route('/metadata/edit', methods=['POST'])
@login_required
def edit_metadata():
    """
    Édite les métadonnées d'un fichier audio
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier invalide'}), 400
            
        # Sauvegarder le fichier
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Gérer l'image de couverture si présente
        cover_path = None
        if 'cover' in request.files:
            cover = request.files['cover']
            if cover.filename:
                cover_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    'covers',
                    secure_filename(cover.filename)
                )
                cover.save(cover_path)
        
        # Récupérer les métadonnées du formulaire
        metadata = request.form.to_dict()
        if cover_path:
            metadata['cover'] = cover_path
        
        # Éditer les métadonnées
        if metadata_manager.edit_metadata(file_path, metadata):
            return jsonify({
                'message': 'Métadonnées mises à jour avec succès',
                'file_path': file_path
            })
        else:
            return jsonify({'error': 'Erreur lors de la mise à jour des métadonnées'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metadata_bp.route('/metadata/extract', methods=['POST'])
@login_required
def extract_metadata():
    """
    Extrait les métadonnées d'un fichier audio
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier invalide'}), 400
            
        # Sauvegarder le fichier temporairement
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp', filename)
        file.save(file_path)
        
        # Extraire les métadonnées
        metadata = metadata_manager.extract_metadata(file_path)
        
        # Nettoyer le fichier temporaire
        os.remove(file_path)
        
        return jsonify(metadata)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metadata_bp.route('/playlists', methods=['POST'])
@login_required
def create_playlist():
    """
    Crée une nouvelle playlist
    """
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return jsonify({'error': 'Nom de playlist requis'}), 400
            
        playlist_id = metadata_manager.create_playlist(name, description)
        return jsonify({
            'message': 'Playlist créée avec succès',
            'playlist_id': playlist_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metadata_bp.route('/playlists/<playlist_id>/tracks', methods=['POST'])
@login_required
def add_to_playlist(playlist_id):
    """
    Ajoute des pistes à une playlist
    """
    try:
        data = request.json
        tracks = data.get('tracks', [])
        
        if not tracks:
            return jsonify({'error': 'Aucune piste fournie'}), 400
            
        if metadata_manager.add_to_playlist(playlist_id, tracks):
            return jsonify({'message': 'Pistes ajoutées avec succès'})
        else:
            return jsonify({'error': 'Playlist non trouvée'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metadata_bp.route('/playlists/<playlist_id>')
@login_required
def get_playlist(playlist_id):
    """
    Récupère les informations d'une playlist
    """
    playlist = metadata_manager.get_playlist(playlist_id)
    if playlist:
        return jsonify(playlist)
    return jsonify({'error': 'Playlist non trouvée'}), 404

@metadata_bp.route('/playlists')
@login_required
def list_playlists():
    """
    Liste toutes les playlists disponibles
    """
    playlists = metadata_manager.list_playlists()
    return jsonify(playlists)
