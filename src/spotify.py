from flask import Blueprint, redirect, url_for, session, request
from spotipy.oauth2 import SpotifyOAuth
import os

spotify = Blueprint('spotify', __name__)

# Configuration Spotify OAuth
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://192.168.0.181:5000/callback/spotify')
SPOTIFY_SCOPE = 'user-library-read playlist-read-private user-read-private'

sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SPOTIFY_SCOPE,
    cache_path='.spotify_token'
)

@spotify.route('/spotify/login')
def spotify_login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@spotify.route('/callback/spotify')
def spotify_callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['spotify_token'] = token_info
    return redirect(url_for('index'))

@spotify.route('/spotify/refresh')
def spotify_refresh():
    if 'spotify_token' not in session:
        return redirect(url_for('spotify.spotify_login'))
    
    token_info = session['spotify_token']
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['spotify_token'] = token_info
    
    return redirect(url_for('index'))
