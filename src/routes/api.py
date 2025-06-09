"""
Routes API pour la gestion de la musique
"""

from flask import Blueprint, jsonify, request, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from ..models.track import Track
from ..database import db

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/tracks', methods=['GET'])
@login_required
def get_tracks():
    """Récupère la liste des pistes"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('q', '')
    sort_by = request.args.get('sort', 'title')
    order = request.args.get('order', 'asc')

    # Construction de la requête
    query = Track.query

    # Filtrage par recherche
    if search:
        query = query.filter(
            db.or_(
                Track.title.ilike(f'%{search}%'),
                Track.artist.ilike(f'%{search}%'),
                Track.album.ilike(f'%{search}%')
            )
        )

    # Tri
    if order == 'desc':
        query = query.order_by(db.desc(getattr(Track, sort_by)))
    else:
        query = query.order_by(getattr(Track, sort_by))

    # Pagination
    pagination = query.paginate(page=page, per_page=per_page)
    tracks = pagination.items

    return jsonify({
        'tracks': [track.to_dict() for track in tracks],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    })

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
