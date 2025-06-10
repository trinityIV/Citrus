"""
Routes API pour la gestion de la musique
"""

from flask import Blueprint, jsonify, request, send_file, current_app, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
import subprocess
import tempfile
from ..models.track import Track
from ..database import db, db_session
from ..utils.query_optimizations import optimize_track_search

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/tracks', methods=['GET'])
@login_required
def get_tracks():
    """Récupère la liste des pistes avec optimisation de la recherche et du cache"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('q', '')
    sort_by = request.args.get('sort', 'title')
    order = request.args.get('order', 'asc')
    
    # Calculer l'offset pour la pagination
    offset = (page - 1) * per_page
    
    try:
        # Si une recherche est effectuée, utiliser notre fonction optimisée
        if search:
            # Utiliser la fonction optimisée avec mise en cache
            start_time = request.environ.get('REQUEST_TIME', None)
            result = optimize_track_search(search, limit=per_page, offset=offset)
            
            # Calculer le nombre total de résultats (approximatif pour la pagination)
            # Note: Ceci pourrait être amélioré en ajoutant un comptage dans la fonction optimize_track_search
            total_count = len(result) + offset
            if len(result) == per_page:
                # S'il y a exactement per_page résultats, il pourrait y en avoir plus
                total_count += 1
                
            # Calculer le nombre de pages
            total_pages = (total_count + per_page - 1) // per_page
            
            # Mesurer le temps de réponse pour le logging
            if start_time:
                elapsed = request.environ.get('REQUEST_TIME', 0) - start_time
                if elapsed > 0.5:  # Si plus de 500ms
                    current_app.logger.info(f"Recherche lente: '{search}' ({elapsed:.2f}s)")
            
            return jsonify({
                'tracks': result,
                'total': total_count,
                'pages': total_pages,
                'current_page': page,
                'per_page': per_page,
                'cached': True  # Indique que les résultats proviennent du cache
            })
        else:
            # Construction de la requête standard pour les listes sans recherche
            query = db_session.query(Track)
            
            # Appliquer le tri
            if hasattr(Track, sort_by):
                if order == 'desc':
                    query = query.order_by(db.desc(getattr(Track, sort_by)))
                else:
                    query = query.order_by(getattr(Track, sort_by))
            else:
                # Tri par défaut si le champ n'existe pas
                query = query.order_by(Track.title)
            
            # Optimiser la requête en sélectionnant uniquement les colonnes nécessaires
            query = query.with_entities(
                Track.id, Track.title, Track.artist, Track.album,
                Track.duration, Track.file_path, Track.created_at
            )
            
            # Exécuter la requête avec pagination
            total_count = query.count()
            tracks = query.limit(per_page).offset(offset).all()
            
            # Calculer le nombre de pages
            total_pages = (total_count + per_page - 1) // per_page
            
            # Convertir les résultats en dictionnaires
            track_dicts = []
            for track in tracks:
                track_dict = {
                    'id': track.id,
                    'title': track.title,
                    'artist': track.artist,
                    'album': track.album,
                    'duration': track.duration,
                    'file_path': track.file_path,
                    'created_at': track.created_at.isoformat() if track.created_at else None
                }
                track_dicts.append(track_dict)
            
            return jsonify({
                'tracks': track_dicts,
                'total': total_count,
                'pages': total_pages,
                'current_page': page,
                'per_page': per_page,
                'cached': False
            })
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des pistes: {str(e)}")
        return jsonify({
            'error': 'Une erreur est survenue lors de la récupération des pistes',
            'message': str(e)
        }), 500

@api_bp.route('/api/tracks/<int:track_id>', methods=['GET'])
@login_required
def get_track(track_id):
    """Récupère les détails d'une piste"""
    track = Track.query.get_or_404(track_id)
    return jsonify(track.to_dict())

@api_bp.route('/api/tracks/<int:track_id>/stream', methods=['GET'])
@login_required
def stream_track(track_id):
    """Stream une piste audio"""
    track = Track.query.get_or_404(track_id)
    return send_file(
        track.file_path,
        mimetype='audio/mpeg',
        as_attachment=False,
        download_name=f"{track.title}.mp3"
    )

@api_bp.route('/api/tracks/<int:track_id>', methods=['PUT'])
@login_required
def update_track(track_id):
    """Met à jour les informations d'une piste"""
    track = Track.query.get_or_404(track_id)
    data = request.get_json()

    # Mise à jour des champs modifiables
    for field in ['title', 'artist', 'album']:
        if field in data:
            setattr(track, field, data[field])

    db.session.commit()
    return jsonify(track.to_dict())

@api_bp.route('/api/tracks/<int:track_id>', methods=['DELETE'])
@login_required
def delete_track(track_id):
    """Supprime une piste"""
    track = Track.query.get_or_404(track_id)
    
    # Suppression du fichier physique
    if os.path.exists(track.file_path):
        os.remove(track.file_path)
    
    db.session.delete(track)
    db.session.commit()
    
    return '', 204

@api_bp.route('/api/tracks/upload', methods=['POST'])
@login_required
def upload_track():
    """Télécharge une nouvelle piste"""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
        
    filename = secure_filename(file.filename)
    file_path = os.path.join('uploads', 'music', filename)
    
    # Création du dossier si nécessaire
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Sauvegarde du fichier
    file.save(file_path)
    
    # Création de l'entrée dans la base de données
    track = Track(
        title=request.form.get('title', filename),
        artist=request.form.get('artist'),
        album=request.form.get('album'),
        file_path=file_path
    )
    
    db.session.add(track)
    db.session.commit()
    
    return jsonify(track.to_dict()), 201


@api_bp.route('/api/library', methods=['GET'])
@login_required
def get_library():
    """Récupère les pistes de la bibliothèque avec pagination et filtrage"""
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    sort_by = request.args.get('sort', 'created_at')
    order = request.args.get('order', 'desc')
    
    try:
        # Construire la requête de base
        query = Track.query
        
        # Appliquer le tri
        if hasattr(Track, sort_by):
            sort_attr = getattr(Track, sort_by)
            if order.lower() == 'desc':
                query = query.order_by(sort_attr.desc())
            else:
                query = query.order_by(sort_attr.asc())
        else:
            # Par défaut, trier par date de création décroissante
            query = query.order_by(Track.created_at.desc())
        
        # Appliquer la pagination
        tracks = query.limit(limit).offset(offset).all()
        
        # Compter le nombre total de pistes pour la pagination
        total_count = Track.query.count()
        
        # Convertir les pistes en dictionnaires
        tracks_data = [{
            'id': track.id,
            'title': track.title,
            'artist': track.artist,
            'album': track.album,
            'duration': track.duration,
            'file_path': track.file_path,
            'created_at': track.created_at.isoformat() if hasattr(track, 'created_at') and track.created_at else None
        } for track in tracks]
        
        return jsonify({
            'tracks': tracks_data,
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération de la bibliothèque: {str(e)}")
        return jsonify({
            'error': 'Erreur lors de la récupération de la bibliothèque',
            'details': str(e)
        }), 500

@api_bp.route('/api/download', methods=['POST'])
@login_required
def download_track():
    """Télécharge une piste audio à partir d'une URL (version simplifiée)"""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL requise'}), 400
    
    url = data['url']
    title = data.get('title', 'Titre inconnu')
    artist = data.get('artist', 'Artiste inconnu')
    
    try:
        # Vérifier si le dossier d'upload existe
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)
        
        # Générer un nom de fichier sécurisé avec timestamp pour éviter les doublons
        import time
        timestamp = int(time.time())
        filename = secure_filename(f"{artist} - {title} - {timestamp}.mp3")
        destination = os.path.join(upload_folder, filename)
        
        # Vérifier si une piste avec ce chemin existe déjà
        existing_track = Track.query.filter_by(file_path=destination).first()
        if existing_track:
            # Si la piste existe déjà, renvoyer ses informations
            return jsonify({
                'success': True,
                'message': 'Piste déjà téléchargée',
                'track': {
                    'id': existing_track.id,
                    'title': existing_track.title,
                    'artist': existing_track.artist,
                    'file_path': existing_track.file_path
                }
            })
        
        # Simuler un téléchargement réussi (pour développement)
        # Dans un environnement de production, vous utiliseriez yt-dlp ou une autre bibliothèque
        # pour télécharger réellement le fichier audio
        
        # Créer un fichier audio vide pour simuler le téléchargement
        with open(destination, 'wb') as f:
            # Écrire quelques octets pour simuler un fichier audio
            f.write(b'\x00' * 1024)
        
        # Créer l'entrée dans la base de données
        track = Track(
            title=title,
            artist=artist,
            album=data.get('album', 'Album inconnu'),
            duration=data.get('duration', 0),
            file_path=destination
        )
        
        db.session.add(track)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Téléchargement simulé avec succès',
            'track': {
                'id': track.id,
                'title': track.title,
                'artist': track.artist,
                'file_path': track.file_path
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Exception lors du téléchargement: {str(e)}")
        return jsonify({
            'error': 'Erreur lors du téléchargement',
            'details': str(e)
        }), 500
