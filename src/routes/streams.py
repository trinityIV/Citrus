"""
Routes pour la gestion des streams (IPTV et Torrents)
"""

from flask import Blueprint, jsonify, request, send_file, Response
from ..utils.auth import login_required
from ..utils.stream_manager import stream_manager
import m3u8
import requests
from pathlib import Path

streams_bp = Blueprint('streams', __name__)

@streams_bp.route('/stream/iptv/add', methods=['POST'])
@login_required
def add_iptv_stream():
    """Ajoute un nouveau stream IPTV"""
    data = request.json
    url = data.get('url')
    name = data.get('name')
    
    if not url:
        return jsonify({'error': 'URL requise'}), 400
        
    try:
        stream_id = stream_manager.add_iptv_stream(url, name)
        return jsonify({
            'stream_id': stream_id,
            'message': 'Stream IPTV ajouté avec succès'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@streams_bp.route('/stream/torrent/add', methods=['POST'])
@login_required
def add_torrent_stream():
    """Ajoute un nouveau stream torrent"""
    if 'torrent' in request.files:
        # Fichier torrent uploadé
        file = request.files['torrent']
        save_path = request.form.get('save_path')
        try:
            stream_id = stream_manager.add_torrent_stream(file.read(), save_path)
            return jsonify({
                'stream_id': stream_id,
                'message': 'Torrent ajouté avec succès'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        # Lien magnet
        data = request.json
        magnet = data.get('magnet')
        save_path = data.get('save_path')
        
        if not magnet:
            return jsonify({'error': 'Lien magnet requis'}), 400
            
        try:
            stream_id = stream_manager.add_torrent_stream(magnet, save_path)
            return jsonify({
                'stream_id': stream_id,
                'message': 'Torrent ajouté avec succès'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@streams_bp.route('/stream/<int:stream_id>/status')
@login_required
def get_stream_status(stream_id):
    """Récupère le statut d'un stream"""
    status = stream_manager.get_stream_status(stream_id)
    if status is None:
        return jsonify({'error': 'Stream non trouvé'}), 404
    return jsonify(status)

@streams_bp.route('/stream/<int:stream_id>/stop', methods=['POST'])
@login_required
def stop_stream(stream_id):
    """Arrête un stream"""
    if stream_manager.stop_stream(stream_id):
        return jsonify({'message': 'Stream arrêté avec succès'})
    return jsonify({'error': 'Erreur lors de l\'arrêt du stream'}), 500

@streams_bp.route('/stream/<int:stream_id>/play')
@login_required
def play_stream(stream_id):
    """Lit un stream"""
    stream = stream_manager.active_streams.get(stream_id)
    if not stream:
        return jsonify({'error': 'Stream non trouvé'}), 404
        
    if stream['type'] == 'iptv':
        # Rediriger vers le flux IPTV
        return redirect(stream['url'])
    elif stream['type'] == 'torrent':
        # Pour les torrents, on renvoie le fichier en streaming
        handle = stream['handle']
        if handle.has_metadata():
            file_path = Path(handle.status().save_path) / handle.get_torrent_info().files().file_path(0)
            return send_file(
                str(file_path),
                mimetype='application/octet-stream',
                as_attachment=False
            )
    
    return jsonify({'error': 'Stream non disponible'}), 404
