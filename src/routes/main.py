"""
Routes principales de l'application
"""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Page d'accueil"""
    # Stats fictives pour le moment
    stats = {
        'tracks': 0,
        'artists': 0,
        'albums': 0,
        'duration': '0h 00m'
    }
    
    # Pistes récentes fictives
    recent_tracks = [
        {
            'title': 'Never Gonna Give You Up',
            'artist': 'Rick Astley',
            'cover_url': '/static/img/default-cover.jpg'
        }
    ]
    
    return render_template('index.html', stats=stats, recent_tracks=recent_tracks)
