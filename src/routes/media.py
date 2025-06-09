"""
Routes pour la gestion des médias (conversion, sous-titres, etc.)
"""

from flask import Blueprint, jsonify, request, send_file
from ..utils.auth import login_required
from ..utils.media_processor import media_processor
from datetime import datetime
import os
from werkzeug.utils import secure_filename

media_bp = Blueprint('media', __name__)

@media_bp.route('/media/convert', methods=['POST'])
@login_required
def convert_media():
    """
    Convertit un fichier média
    """
    try:
        # Vérifier si un fichier est présent
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier invalide'}), 400
            
        # Récupérer les paramètres
        output_format = request.form.get('format', 'mp3')
        quality = request.form.get('quality', 'high')
        schedule_time = request.form.get('schedule_time')
        
        # Gérer les sous-titres
        subtitle_path = None
        if 'subtitles' in request.files:
            subtitle_file = request.files['subtitles']
            if subtitle_file.filename:
                subtitle_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    'subtitles',
                    secure_filename(subtitle_file.filename)
                )
                subtitle_file.save(subtitle_path)
        
        # Sauvegarder le fichier d'entrée
        input_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            'temp',
            secure_filename(file.filename)
        )
        file.save(input_path)
        
        # Convertir le fichier
        if schedule_time:
            schedule_dt = datetime.strptime(schedule_time, '%Y-%m-%d %H:%M')
            result = media_processor.convert_media(
                input_path, 
                output_format,
                subtitle_path=subtitle_path,
                quality=quality,
                schedule_time=schedule_dt
            )
            return jsonify({
                'message': 'Conversion programmée',
                'schedule_time': schedule_time
            })
        else:
            output_path = media_processor.convert_media(
                input_path,
                output_format,
                subtitle_path=subtitle_path,
                quality=quality
            )
            return jsonify({
                'message': 'Conversion démarrée',
                'output_path': output_path
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/conversion/<conversion_id>/status')
@login_required
def get_conversion_status(conversion_id):
    """
    Récupère le statut d'une conversion
    """
    status = media_processor.get_conversion_status(conversion_id)
    return jsonify(status)

@media_bp.route('/media/bandwidth', methods=['POST'])
@login_required
def set_bandwidth_limit():
    """
    Définit une limite de bande passante
    """
    try:
        limit = request.json.get('limit')
        if limit is None:
            return jsonify({'error': 'Limite non spécifiée'}), 400
            
        media_processor.set_bandwidth_limit(int(limit))
        return jsonify({'message': 'Limite de bande passante mise à jour'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@media_bp.route('/media/stats')
@login_required
def get_system_stats():
    """
    Récupère les statistiques système
    """
    stats = media_processor.get_system_stats()
    return jsonify(stats)
