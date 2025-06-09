"""
Routes pour l'IPTV.
Gère l'accès aux flux IPTV.
"""

from flask import Blueprint, jsonify, request
from services.iptv_scraper import IPTVScraper

bp = Blueprint('iptv', __name__, url_prefix='/api/iptv')
scraper = IPTVScraper()

@bp.route('/streams', methods=['GET'])
async def get_streams():
    """Récupère la liste des flux disponibles"""
    force_update = request.args.get('force', '').lower() == 'true'
    streams = await scraper.get_streams(force_update=force_update)
    return jsonify(streams)

@bp.route('/check/<path:url>', methods=['GET'])
async def check_stream(url):
    """Vérifie si un flux est accessible"""
    is_active = await scraper.check_stream(url)
    return jsonify({
        'url': url,
        'active': is_active
    })

@bp.route('/categories', methods=['GET'])
async def get_categories():
    """Récupère les catégories de flux disponibles"""
    streams = await scraper.get_streams()
    categories = {}
    
    for stream in streams:
        source = stream['source']
        if source not in categories:
            categories[source] = {
                'name': source,
                'count': 0,
                'formats': set()
            }
        categories[source]['count'] += 1
        categories[source]['formats'].add(stream['format'])
    
    # Convertir les sets en listes pour la sérialisation JSON
    for cat in categories.values():
        cat['formats'] = list(cat['formats'])
    
    return jsonify(list(categories.values()))
