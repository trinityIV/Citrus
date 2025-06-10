"""
Routes pour la gestion des playlists
"""

import os
import time
from flask import Blueprint, jsonify, request, render_template, current_app, g
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload, load_only
from sqlalchemy import and_, desc, func
from ..models.playlist import Playlist, playlist_tracks
from ..models.track import Track
from ..database import db_session
from ..utils.auth import login_required
from ..utils.image import save_image, delete_image
from ..utils.query_optimizations import optimize_playlist_tracks_query, get_user_playlists_optimized

# Création du blueprint
playlists_bp = Blueprint('playlists', __name__)

# Routes pour les vues
@playlists_bp.route('/playlists')
@login_required
def playlists_page():
    """Page des playlists"""
    return render_template('playlists.html')

# Routes API
@playlists_bp.route('/api/playlists', methods=['GET'])
@login_required
def get_playlists():
    """Récupère toutes les playlists de l'utilisateur avec pagination et optimisation"""
    try:
        # Paramètres de pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 50)  # Limiter à 50 éléments maximum par page
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        
        # Utiliser la fonction optimisée avec mise en cache
        result = get_user_playlists_optimized(request.user.id, page=page, per_page=per_page)
        
        # Mesurer le temps de réponse pour le logging
        elapsed = time.time() - start_time
        if elapsed > 0.5:  # Si plus de 500ms
            current_app.logger.info(f"Récupération lente des playlists: user_id={request.user.id} ({elapsed:.2f}s)")
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des playlists: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@playlists_bp.route('/api/playlists/<int:playlist_id>', methods=['GET'])
@login_required
def get_playlist(playlist_id):
    """Récupère une playlist spécifique avec ses pistes"""
    try:
        # Utiliser get() avec un filtre au lieu de filter_by().first_or_404()
        # C'est plus efficace car cela génère une requête SQL avec une clause WHERE sur la clé primaire
        playlist = (
            db_session.get(Playlist, playlist_id)
        )
        
        # Vérifier si la playlist existe et appartient à l'utilisateur
        if not playlist or playlist.user_id != request.user.id:
            return jsonify({'error': 'Playlist non trouvée'}), 404
            
        # Charger les pistes de manière optimisée
        # Utiliser une requête séparée avec joinedload pour éviter le problème N+1
        db_session.query(Track).join(
            playlist_tracks, 
            (Track.id == playlist_tracks.c.track_id) & (playlist_tracks.c.playlist_id == playlist_id)
        ).options(
            # Charger uniquement les colonnes nécessaires
            load_only(Track.id, Track.title, Track.artist, Track.album, Track.duration, Track.file_path)
        ).order_by(playlist_tracks.c.position).all()
        
        return jsonify(playlist.to_dict())
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération de la playlist {playlist_id}: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@playlists_bp.route('/api/playlists', methods=['POST'])
@login_required
def create_playlist():
    """Crée une nouvelle playlist"""
    try:
        # Récupérer les données
        name = request.form.get('name')
        description = request.form.get('description', '')
        cover_image = request.files.get('cover_image')

        if not name:
            return jsonify({'error': 'Le nom est requis'}), 400

        # Créer la playlist
        playlist = Playlist(
            name=name,
            description=description,
            user_id=request.user.id
        )

        # Gérer l'image de couverture
        if cover_image:
            filename = save_image(
                cover_image,
                'playlists',
                allowed_extensions={'png', 'jpg', 'jpeg', 'gif'},
                max_size=5 * 1024 * 1024  # 5MB
            )
            if filename:
                playlist.cover_image = filename

        # Sauvegarder
        db_session.add(playlist)
        db_session.commit()

        return jsonify(playlist.to_dict()), 201

    except Exception as e:
        db_session.rollback()
        current_app.logger.error(f"Erreur lors de la création de la playlist: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@playlists_bp.route('/api/playlists/<int:playlist_id>', methods=['PUT'])
@login_required
def update_playlist(playlist_id):
    """Met à jour une playlist"""
    try:
        playlist = (
            Playlist.query
            .filter_by(id=playlist_id, user_id=request.user.id)
            .first_or_404()
        )

        # Mettre à jour les champs
        if 'name' in request.form:
            playlist.name = request.form['name']
        if 'description' in request.form:
            playlist.description = request.form['description']

        # Gérer l'image de couverture
        if 'cover_image' in request.files:
            # Supprimer l'ancienne image
            if playlist.cover_image:
                delete_image(playlist.cover_image, 'playlists')

            # Sauvegarder la nouvelle image
            filename = save_image(
                request.files['cover_image'],
                'playlists',
                allowed_extensions={'png', 'jpg', 'jpeg', 'gif'},
                max_size=5 * 1024 * 1024
            )
            if filename:
                playlist.cover_image = filename

        db_session.commit()
        return jsonify(playlist.to_dict())

    except Exception as e:
        db_session.rollback()
        current_app.logger.error(f"Erreur lors de la mise à jour de la playlist {playlist_id}: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@playlists_bp.route('/api/playlists/<int:playlist_id>', methods=['DELETE'])
@login_required
def delete_playlist(playlist_id):
    """Supprime une playlist"""
    try:
        playlist = (
            Playlist.query
            .filter_by(id=playlist_id, user_id=request.user.id)
            .first_or_404()
        )

        # Supprimer l'image de couverture
        if playlist.cover_image:
            delete_image(playlist.cover_image, 'playlists')

        db_session.delete(playlist)
        db_session.commit()

        return '', 204

    except Exception as e:
        db_session.rollback()
        current_app.logger.error(f"Erreur lors de la suppression de la playlist {playlist_id}: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@playlists_bp.route('/api/playlists/<int:playlist_id>/tracks', methods=['GET'])
@login_required
def get_playlist_tracks(playlist_id):
    """Récupère les pistes d'une playlist avec pagination et optimisation"""
    try:
        # Vérifier si la playlist existe et appartient à l'utilisateur
        playlist = db_session.get(Playlist, playlist_id)
        
        if not playlist or playlist.user_id != request.user.id:
            return jsonify({'error': 'Playlist non trouvée ou accès non autorisé'}), 404
        
        # Paramètres de pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 50)  # Limiter à 50 éléments maximum par page
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        
        # Utiliser la fonction optimisée avec mise en cache
        result = optimize_playlist_tracks_query(playlist_id, page=page, per_page=per_page)
        
        # Ajouter des informations sur la playlist
        result['playlist'] = {
            'id': playlist.id,
            'name': playlist.name,
            'description': playlist.description,
            'image_path': playlist.image_path
        }
        
        # Mesurer le temps de réponse pour le logging
        elapsed = time.time() - start_time
        if elapsed > 0.5:  # Si plus de 500ms
            current_app.logger.info(f"Récupération lente des pistes de playlist: id={playlist_id} ({elapsed:.2f}s)")
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des pistes de la playlist {playlist_id}: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@playlists_bp.route('/api/playlists/<int:playlist_id>/tracks', methods=['POST'])
@login_required
def add_track_to_playlist(playlist_id):
    """Ajoute une piste à une playlist"""
    try:
        data = request.get_json()
        if not data or 'track_id' not in data:
            return jsonify({'error': 'ID de piste requis'}), 400

        playlist = (
            Playlist.query
            .filter_by(id=playlist_id, user_id=request.user.id)
            .first_or_404()
        )

        track = Track.query.get_or_404(data['track_id'])
        position = data.get('position')

        playlist.add_track(track, position)
        db_session.commit()

        return jsonify({'message': 'Piste ajoutée avec succès'})

    except Exception as e:
        db_session.rollback()
        current_app.logger.error(f"Erreur lors de l'ajout de la piste à la playlist {playlist_id}: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@playlists_bp.route('/api/playlists/<int:playlist_id>/tracks/<int:track_id>', methods=['DELETE'])
@login_required
def remove_track_from_playlist(playlist_id, track_id):
    """Retire une piste d'une playlist"""
    try:
        playlist = (
            Playlist.query
            .filter_by(id=playlist_id, user_id=request.user.id)
            .first_or_404()
        )

        track = Track.query.get_or_404(track_id)
        playlist.remove_track(track)
        db_session.commit()

        return '', 204

    except Exception as e:
        db_session.rollback()
        current_app.logger.error(f"Erreur lors de la suppression de la piste de la playlist {playlist_id}: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@playlists_bp.route('/api/playlists/<int:playlist_id>/tracks/reorder', methods=['POST'])
@login_required
def reorder_playlist_tracks(playlist_id):
    """Réorganise les pistes d'une playlist"""
    try:
        data = request.get_json()
        if not data or 'track_id' not in data or 'position' not in data:
            return jsonify({'error': 'ID de piste et position requis'}), 400

        playlist = (
            Playlist.query
            .filter_by(id=playlist_id, user_id=request.user.id)
            .first_or_404()
        )

        track = Track.query.get_or_404(data['track_id'])
        playlist.set_track_position(track, data['position'])
        db_session.commit()

        return jsonify({'message': 'Position mise à jour avec succès'})

    except Exception as e:
        db_session.rollback()
        current_app.logger.error(f"Erreur lors de la réorganisation des pistes de la playlist {playlist_id}: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500
