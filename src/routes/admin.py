"""
Routes pour l'administration et la maintenance
"""

from flask import Blueprint, jsonify, render_template, request, current_app
from flask_login import login_required
from sqlalchemy import text, func
from ..database import db_session
from ..models.user import User
from ..models.track import Track
from ..models.playlist import Playlist
from ..utils.db_optimizations import get_db_stats, optimize_db, query_cache

# Création du blueprint
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
def admin_page():
    """Page d'administration"""
    # Vérifier si l'utilisateur est un administrateur
    if not request.user.is_admin:
        return render_template('error.html', error="Accès non autorisé"), 403
    
    return render_template('admin.html', title='Administration')

@admin_bp.route('/api/admin/stats', methods=['GET'])
@login_required
def get_stats():
    """Récupère les statistiques du système"""
    # Vérifier si l'utilisateur est un administrateur
    if not hasattr(request.user, 'is_admin') or not request.user.is_admin:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        # Statistiques de la base de données
        db_stats = get_db_stats()
        
        # Statistiques du cache de requêtes
        cache_stats = query_cache.get_stats()
        
        # Statistiques des utilisateurs
        user_count = db_session.query(func.count(User.id)).scalar()
        
        # Statistiques des pistes
        track_count = db_session.query(func.count(Track.id)).scalar()
        track_size = db_session.query(func.sum(Track.file_size)).scalar() or 0
        
        # Statistiques des playlists
        playlist_count = db_session.query(func.count(Playlist.id)).scalar()
        
        stats = {
            'database': db_stats,
            'cache': cache_stats,
            'users': {
                'count': user_count
            },
            'tracks': {
                'count': track_count,
                'total_size': track_size,
                'avg_size': track_size / track_count if track_count > 0 else 0
            },
            'playlists': {
                'count': playlist_count
            }
        }
        
        return jsonify(stats)
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des statistiques: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@admin_bp.route('/api/admin/optimize', methods=['POST'])
@login_required
def optimize_database():
    """Optimise la base de données"""
    # Vérifier si l'utilisateur est un administrateur
    if not hasattr(request.user, 'is_admin') or not request.user.is_admin:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        # Optimiser la base de données
        results = optimize_db()
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'optimisation de la base de données: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@admin_bp.route('/api/admin/cache/clear', methods=['POST'])
@login_required
def clear_cache():
    """Vide le cache de requêtes"""
    # Vérifier si l'utilisateur est un administrateur
    if not hasattr(request.user, 'is_admin') or not request.user.is_admin:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        # Vider le cache
        query_cache.clear()
        
        return jsonify({
            'success': True,
            'message': 'Cache vidé avec succès'
        })
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors du vidage du cache: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500

@admin_bp.route('/api/admin/slow-queries', methods=['GET'])
@login_required
def get_slow_queries():
    """Récupère les requêtes lentes"""
    # Vérifier si l'utilisateur est un administrateur
    if not hasattr(request.user, 'is_admin') or not request.user.is_admin:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    try:
        # Cette fonctionnalité nécessite une extension SQLite pour le suivi des requêtes
        # Pour l'instant, nous retournons un message d'information
        return jsonify({
            'message': 'Cette fonctionnalité nécessite une configuration supplémentaire',
            'queries': []
        })
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors de la récupération des requêtes lentes: {str(e)}")
        return jsonify({'error': 'Erreur serveur'}), 500
