"""
Optimisations spécifiques pour les requêtes de recherche et de filtrage
"""

from typing import List, Dict, Any, Optional, Union
from sqlalchemy import or_, and_, func, desc
from sqlalchemy.orm import Query, contains_eager, joinedload, load_only
from ..models.track import Track
from ..models.playlist import Playlist, playlist_tracks
from ..utils.db_optimizations import cached_query

def optimize_track_search(query: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Recherche optimisée de pistes par titre, artiste ou album
    
    Args:
        query: Terme de recherche
        limit: Nombre maximum de résultats
        offset: Décalage pour la pagination
        
    Returns:
        Liste de pistes correspondant à la recherche
    """
    # Normaliser la requête
    search_term = f"%{query.lower()}%"
    
    # Utiliser la fonction cached_query pour mettre en cache les résultats
    return _perform_track_search(search_term, limit, offset)

@cached_query(ttl=300)  # Cache de 5 minutes
def _perform_track_search(search_term: str, limit: int, offset: int) -> List[Dict[str, Any]]:
    """
    Effectue la recherche de pistes avec mise en cache
    """
    from ..database import db_session
    
    # Construire la requête optimisée
    query = (
        db_session.query(Track)
        .filter(
            or_(
                func.lower(Track.title).like(search_term),
                func.lower(Track.artist).like(search_term),
                func.lower(Track.album).like(search_term)
            )
        )
        .options(
            # Charger uniquement les colonnes nécessaires
            load_only(
                Track.id, Track.title, Track.artist, Track.album,
                Track.duration, Track.file_path
            )
        )
        .order_by(desc(Track.created_at))
        .limit(limit)
        .offset(offset)
    )
    
    # Exécuter la requête
    tracks = query.all()
    
    # Convertir les résultats en dictionnaires
    return [track.to_dict() for track in tracks]

def optimize_playlist_tracks_query(playlist_id: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """
    Récupère les pistes d'une playlist avec pagination optimisée
    
    Args:
        playlist_id: ID de la playlist
        page: Numéro de page
        per_page: Nombre d'éléments par page
        
    Returns:
        Dictionnaire contenant les pistes et les informations de pagination
    """
    from ..database import db_session
    
    # Calculer l'offset
    offset = (page - 1) * per_page
    
    # Requête pour récupérer le nombre total de pistes
    total_count = (
        db_session.query(func.count())
        .select_from(playlist_tracks)
        .filter(playlist_tracks.c.playlist_id == playlist_id)
        .scalar()
    )
    
    # Requête optimisée pour récupérer les pistes avec leur position
    tracks_query = (
        db_session.query(Track, playlist_tracks.c.position)
        .join(
            playlist_tracks,
            and_(
                Track.id == playlist_tracks.c.track_id,
                playlist_tracks.c.playlist_id == playlist_id
            )
        )
        .options(
            # Charger uniquement les colonnes nécessaires
            load_only(
                Track.id, Track.title, Track.artist, Track.album,
                Track.duration, Track.file_path
            )
        )
        .order_by(playlist_tracks.c.position)
        .limit(per_page)
        .offset(offset)
    )
    
    # Exécuter la requête
    results = tracks_query.all()
    
    # Convertir les résultats en dictionnaires
    tracks = []
    for track, position in results:
        track_dict = track.to_dict()
        track_dict['position'] = position
        tracks.append(track_dict)
    
    # Calculer les informations de pagination
    total_pages = (total_count + per_page - 1) // per_page if per_page > 0 else 1
    
    return {
        'items': tracks,
        'total': total_count,
        'pages': total_pages,
        'page': page,
        'per_page': per_page,
        'has_next': page < total_pages,
        'has_prev': page > 1
    }

def get_user_playlists_optimized(user_id: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """
    Récupère les playlists d'un utilisateur avec pagination optimisée
    
    Args:
        user_id: ID de l'utilisateur
        page: Numéro de page
        per_page: Nombre d'éléments par page
        
    Returns:
        Dictionnaire contenant les playlists et les informations de pagination
    """
    from ..database import db_session
    
    # Calculer l'offset
    offset = (page - 1) * per_page
    
    # Requête pour récupérer le nombre total de playlists
    total_count = (
        db_session.query(func.count(Playlist.id))
        .filter(Playlist.user_id == user_id)
        .scalar()
    )
    
    # Requête optimisée pour récupérer les playlists avec le nombre de pistes
    subquery = (
        db_session.query(
            playlist_tracks.c.playlist_id,
            func.count(playlist_tracks.c.track_id).label('track_count')
        )
        .group_by(playlist_tracks.c.playlist_id)
        .subquery()
    )
    
    playlists_query = (
        db_session.query(Playlist, func.coalesce(subquery.c.track_count, 0))
        .outerjoin(subquery, Playlist.id == subquery.c.playlist_id)
        .filter(Playlist.user_id == user_id)
        .order_by(desc(Playlist.updated_at))
        .limit(per_page)
        .offset(offset)
    )
    
    # Exécuter la requête
    results = playlists_query.all()
    
    # Convertir les résultats en dictionnaires
    playlists = []
    for playlist, track_count in results:
        playlist_dict = playlist.to_dict()
        playlist_dict['track_count'] = track_count
        playlists.append(playlist_dict)
    
    # Calculer les informations de pagination
    total_pages = (total_count + per_page - 1) // per_page if per_page > 0 else 1
    
    return {
        'items': playlists,
        'total': total_count,
        'pages': total_pages,
        'page': page,
        'per_page': per_page,
        'has_next': page < total_pages,
        'has_prev': page > 1
    }
