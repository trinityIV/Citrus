"""
Utilitaires pour l'authentification
"""

from functools import wraps
from flask import request, jsonify, session, current_app
from ..models.user import User

def login_required(f):
    """
    Décorateur pour protéger les routes qui nécessitent une authentification
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérifier si l'utilisateur est connecté
        if 'user_id' not in session:
            return jsonify({'error': 'Authentification requise'}), 401

        # Récupérer l'utilisateur
        user = User.query.get(session['user_id'])
        if not user:
            session.pop('user_id', None)
            return jsonify({'error': 'Utilisateur non trouvé'}), 401

        # Ajouter l'utilisateur à l'objet request
        request.user = user
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """
    Retourne l'utilisateur actuellement connecté ou None
    """
    if 'user_id' in session:
        return User.query.get(session['user_id'])
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
