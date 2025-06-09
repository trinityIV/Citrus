"""
Utilitaires pour l'API Spotify
"""
import yt_dlp
from typing import Dict, Any

def get_spotify_info(url: str) -> Dict[str, Any]:
    """Récupère les informations d'une piste ou playlist Spotify via yt-dlp (si supporté)."""
    ydl_opts = {'quiet': True, 'extract_flat': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        raise RuntimeError(f"yt-dlp ne supporte pas ce lien Spotify ou erreur: {e}")
