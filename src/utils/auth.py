"""
Utilitaires pour l'authentification
"""

from functools import wraps
from flask import request, jsonify, session, current_app, g
from ..models.user import User
from ..database import db_session
import time

def login_required(f):
    """
    Décorateur pour protéger les routes qui nécessitent une authentification
    Optimisé avec mise en cache de l'utilisateur dans g
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérifier si l'utilisateur est connecté
        if 'user_id' not in session:
            return jsonify({'error': 'Authentification requise'}), 401

        # Récupérer l'utilisateur depuis le cache ou la base de données
        user_id = session['user_id']
        
        # Vérifier si l'utilisateur est déjà en cache dans g
        if not hasattr(g, 'user_cache'):
            g.user_cache = {}
            g.user_cache_time = {}
        
        current_time = time.time()
        cache_ttl = 60  # 60 secondes de TTL pour le cache
        
        # Vérifier si l'utilisateur est en cache et si le cache est encore valide
        if user_id in g.user_cache and current_time - g.user_cache_time.get(user_id, 0) < cache_ttl:
            user = g.user_cache[user_id]
        else:
            # Utiliser db.session.get qui est plus efficace pour les clés primaires
            user = db_session.get(User, user_id)
            
            # Mettre en cache l'utilisateur
            if user:
                g.user_cache[user_id] = user
                g.user_cache_time[user_id] = current_time
        
        if not user:
            session.pop('user_id', None)
            if user_id in g.user_cache:
                del g.user_cache[user_id]
                if user_id in g.user_cache_time:
                    del g.user_cache_time[user_id]
            return jsonify({'error': 'Utilisateur non trouvé'}), 401

        # Ajouter l'utilisateur à l'objet request
        request.user = user
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """
    Retourne l'utilisateur actuellement connecté ou None
    Optimisé avec mise en cache
    """
    if 'user_id' in session:
        user_id = session['user_id']
        
        # Vérifier si l'utilisateur est déjà en cache dans g
        if hasattr(g, 'user_cache') and user_id in g.user_cache:
            # Vérifier si le cache est encore valide
            current_time = time.time()
            cache_ttl = 60  # 60 secondes de TTL pour le cache
            
            if current_time - g.user_cache_time.get(user_id, 0) < cache_ttl:
                return g.user_cache[user_id]
        
        # Utiliser db.session.get qui est plus efficace pour les clés primaires
        user = db_session.get(User, user_id)
        
        # Mettre en cache l'utilisateur
        if user:
            if not hasattr(g, 'user_cache'):
                g.user_cache = {}
                g.user_cache_time = {}
                
            g.user_cache[user_id] = user
            g.user_cache_time[user_id] = time.time()
            
        return user
    return None

def is_authenticated():
    """
    Vérifie si l'utilisateur est authentifié
    """
    return 'user_id' in session

def login_user(user):
    """
    Connecte un utilisateur
    """
    session['user_id'] = user.id
    session.permanent = True  # Le cookie de session expirera après PERMANENT_SESSION_LIFETIME

def logout_user():
    """
    Déconnecte l'utilisateur actuel
    """
    session.pop('user_id', None)
    session.clear()
