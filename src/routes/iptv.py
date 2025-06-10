"""
Routes pour l'IPTV.
Gère l'accès aux flux IPTV.
"""

from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required
from ..services.iptv_scraper import IPTVScraper

iptv_bp = Blueprint('iptv', __name__)
scraper = IPTVScraper()

@iptv_bp.route('/iptv')
@login_required
def iptv():
    """Page principale IPTV"""
    return render_template('iptv.html', title='IPTV')

# API Routes
@iptv_bp.route('/api/iptv/streams', methods=['GET'])
@login_required

async def get_streams():
    """Récupère la liste des flux disponibles"""
    force_update = request.args.get('force', '').lower() == 'true'
    streams = await scraper.get_streams(force_update=force_update)
    return jsonify(streams)

@iptv_bp.route('/api/iptv/check/<path:url>', methods=['GET'])
@login_required
async def check_stream(url):
    """Vérifie si un flux est accessible"""
    is_active = await scraper.check_stream(url)
    return jsonify({
        'url': url,
        'active': is_active
    })

@iptv_bp.route('/api/iptv/categories', methods=['GET'])
@login_required
async def get_categories():
    """Récupère les catégories de flux disponibles"""
    categories = await scraper.get_categories()
    
    # Formater la réponse
    result = []
    for cat, count in categories.items():
        result.append({
            'name': cat,
            'count': count,
            'url': f'/api/iptv/category/{cat}'
        })
    
    return jsonify({
        'status': 'success',
        'data': result,
        'total': len(result)
    })
    
    return jsonify(list(categories.values()))
