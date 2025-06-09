"""
Routes pour l'authentification Spotify
"""

from flask import Blueprint, redirect, request, url_for, session, current_app
from flask_login import login_required, current_user
from ..services.spotify import SpotifyService
from ..database import db

spotify_bp = Blueprint('spotify', __name__)

@spotify_bp.route('/auth/spotify/login')
@login_required
def spotify_login():
    """Redirige vers la page de connexion Spotify"""
    spotify = SpotifyService()
    auth_url = spotify.get_auth_url()
    return redirect(auth_url)

@spotify_bp.route('/auth/spotify/callback')
@login_required
def spotify_callback():
    """Callback après authentification Spotify"""
    error = request.args.get('error')
    if error:
        return f"Erreur d'authentification Spotify: {error}"
    
    code = request.args.get('code')
    spotify = SpotifyService()
    
    # Récupérer les tokens
    token_info = spotify.get_access_token(code)
    
    # Stocker les tokens dans la session
    session['spotify_token'] = token_info.get('access_token')
    session['spotify_refresh_token'] = token_info.get('refresh_token')
    
    return redirect(url_for('main.index'))

@spotify_bp.route('/auth/spotify/refresh')
@login_required
def spotify_refresh():
    """Rafraîchit le token Spotify"""
    spotify = SpotifyService()
    refresh_token = session.get('spotify_refresh_token')
    
    if not refresh_token:
        return redirect(url_for('spotify.spotify_login'))
    
    token_info = spotify.refresh_token(refresh_token)
    session['spotify_token'] = token_info.get('access_token')
    
    return redirect(request.referrer or url_for('main.index'))
