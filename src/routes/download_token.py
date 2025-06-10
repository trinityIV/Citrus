"""
Routes pour la gestion des tokens de téléchargement
Permet le téléchargement via QR code et liens partagés
"""

import os
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, jsonify, request, current_app, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# Créer le blueprint
download_token_bp = Blueprint('download_token', __name__)

# Stockage des tokens (en mémoire pour la démo, à remplacer par une base de données en production)
# Structure: {token: {type, ids, expiry, user_id}}
tokens = {}

@download_token_bp.route('/api/download-token', methods=['POST'])
@login_required
def create_download_token():
    """Crée un token temporaire pour le téléchargement"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400
    
    download_type = data.get('type')
    
    if download_type not in ['single', 'batch']:
        return jsonify({'error': 'Type de téléchargement invalide'}), 400
    
    # Valider les IDs selon le type
    if download_type == 'single' and 'id' not in data:
        return jsonify({'error': 'ID de piste manquant'}), 400
    
    if download_type == 'batch' and (not data.get('ids') or not isinstance(data.get('ids'), list)):
        return jsonify({'error': 'Liste d\'IDs invalide'}), 400
    
    # Créer un token unique
    token = str(uuid.uuid4())
    
    # Stocker les informations du token (expire après 24h)
    tokens[token] = {
        'type': download_type,
        'id': data.get('id'),
        'ids': data.get('ids'),
        'user_id': current_user.id,
        'expiry': datetime.now() + timedelta(hours=24)
    }
    
    return jsonify({
        'token': token,
        'expires_in': '24 heures'
    })

@download_token_bp.route('/download/<token>', methods=['GET'])
def download_by_token(token):
    """Télécharge un fichier à partir d'un token"""
    # Vérifier si le token existe
    if token not in tokens:
        abort(404, description="Token de téléchargement invalide ou expiré")
    
    token_data = tokens[token]
    
    # Vérifier si le token n'a pas expiré
    if datetime.now() > token_data['expiry']:
        # Supprimer le token expiré
        del tokens[token]
        abort(410, description="Ce lien de téléchargement a expiré")
    
    try:
        # Préparer le téléchargement selon le type
        if token_data['type'] == 'single':
            # Téléchargement d'une seule piste
            track_id = token_data['id']
            
            # Ici, vous devriez récupérer les informations de la piste depuis votre base de données
            # Pour cet exemple, nous simulons un chemin de fichier
            from ..models.track import Track
            track = Track.query.get(track_id)
            
            if not track:
                abort(404, description="Piste introuvable")
            
            # Vérifier si le fichier existe
            if not os.path.exists(track.file_path):
                abort(404, description="Fichier audio introuvable")
            
            # Envoyer le fichier
            return send_file(
                track.file_path,
                as_attachment=True,
                download_name=secure_filename(f"{track.artist} - {track.title}.mp3")
            )
        
        elif token_data['type'] == 'batch':
            # Téléchargement par lots (ZIP)
            track_ids = token_data['ids']
            
            # Créer un ZIP temporaire avec les pistes
            from ..services.download import create_zip_from_tracks
            zip_path, zip_filename = create_zip_from_tracks(track_ids)
            
            # Envoyer le fichier ZIP
            return send_file(
                zip_path,
                as_attachment=True,
                download_name=zip_filename
            )
    
    except Exception as e:
        current_app.logger.error(f"Erreur lors du téléchargement par token: {str(e)}")
        abort(500, description="Erreur lors de la préparation du téléchargement")
    
    # Supprimer le token après utilisation (usage unique)
    del tokens[token]

@download_token_bp.route('/api/send-download-link', methods=['POST'])
@login_required
def send_download_link():
    """Envoie un lien de téléchargement par email"""
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'error': 'Email manquant'}), 400
    
    email = data.get('email')
    download_type = data.get('type')
    
    # Valider les données
    if download_type not in ['single', 'batch']:
        return jsonify({'error': 'Type de téléchargement invalide'}), 400
    
    # Créer un token pour ce téléchargement
    token = str(uuid.uuid4())
    
    # Stocker les informations du token
    tokens[token] = {
        'type': download_type,
        'id': data.get('id'),
        'ids': data.get('ids'),
        'user_id': current_user.id,
        'expiry': datetime.now() + timedelta(days=7)  # Expire après 7 jours
    }
    
    # Construire l'URL de téléchargement
    download_url = f"{request.host_url.rstrip('/')}/download/{token}"
    
    try:
        # Envoyer l'email avec le lien de téléchargement
        from ..services.email import send_email
        
        # Déterminer le sujet et le contenu selon le type de téléchargement
        if download_type == 'single':
            from ..models.track import Track
            track = Track.query.get(data.get('id'))
            
            if not track:
                return jsonify({'error': 'Piste introuvable'}), 404
            
            subject = f"Votre téléchargement Citrus Music: {track.title}"
            content = f"""
            <h2>Votre musique est prête à être téléchargée!</h2>
            <p>Vous avez demandé le téléchargement de <strong>{track.title}</strong> par <strong>{track.artist}</strong>.</p>
            <p>Cliquez sur le lien ci-dessous pour télécharger votre musique:</p>
            <p><a href="{download_url}">{download_url}</a></p>
            <p>Ce lien expirera dans 7 jours.</p>
            <p>Merci d'utiliser Citrus Music Server!</p>
            """
        else:
            # Téléchargement par lots
            track_count = len(data.get('ids', []))
            subject = f"Votre téléchargement groupé Citrus Music ({track_count} pistes)"
            content = f"""
            <h2>Vos musiques sont prêtes à être téléchargées!</h2>
            <p>Vous avez demandé le téléchargement de <strong>{track_count} pistes</strong>.</p>
            <p>Cliquez sur le lien ci-dessous pour télécharger votre archive ZIP:</p>
            <p><a href="{download_url}">{download_url}</a></p>
            <p>Ce lien expirera dans 7 jours.</p>
            <p>Merci d'utiliser Citrus Music Server!</p>
            """
        
        # Simuler l'envoi d'email (à remplacer par un vrai service d'email)
        # send_email(email, subject, content)
        
        # Pour la démo, on simule un envoi réussi
        current_app.logger.info(f"Email envoyé à {email} avec le lien {download_url}")
        
        return jsonify({
            'success': True,
            'message': f'Lien de téléchargement envoyé à {email}'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erreur lors de l'envoi de l'email: {str(e)}")
        return jsonify({'error': 'Erreur lors de l\'envoi de l\'email'}), 500
