"""
Utilitaires pour la gestion des images
"""

import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app

def save_image(file, folder, allowed_extensions=None, max_size=None, max_dimensions=None):
    """
    Sauvegarde une image téléchargée
    
    Args:
        file: Fichier image (FileStorage)
        folder: Dossier de destination (ex: 'playlists', 'covers')
        allowed_extensions: Extensions autorisées (set)
        max_size: Taille maximale en octets (int)
        max_dimensions: Dimensions maximales (tuple)
    
    Returns:
        str: Nom du fichier sauvegardé ou None si erreur
    """
    try:
        if not file:
            return None

        # Vérifier l'extension
        if allowed_extensions:
            extension = file.filename.rsplit('.', 1)[1].lower()
            if extension not in allowed_extensions:
                current_app.logger.warning(f"Extension non autorisée: {extension}")
                return None

        # Vérifier la taille
        if max_size and file.content_length > max_size:
            current_app.logger.warning(f"Fichier trop volumineux: {file.content_length} octets")
            return None

        # Créer un nom de fichier unique
        filename = secure_filename(file.filename)
        unique_filename = f"{str(uuid.uuid4())}_{filename}"

        # Créer le dossier de destination s'il n'existe pas
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
        os.makedirs(upload_folder, exist_ok=True)

        # Chemin complet du fichier
        filepath = os.path.join(upload_folder, unique_filename)

        # Sauvegarder le fichier
        file.save(filepath)

        # Redimensionner si nécessaire
        if max_dimensions:
            try:
                with Image.open(filepath) as img:
                    if img.size[0] > max_dimensions[0] or img.size[1] > max_dimensions[1]:
                        img.thumbnail(max_dimensions)
                        img.save(filepath)
            except Exception as e:
                current_app.logger.error(f"Erreur lors du redimensionnement: {str(e)}")
                os.remove(filepath)
                return None

        return unique_filename

    except Exception as e:
        current_app.logger.error(f"Erreur lors de la sauvegarde de l'image: {str(e)}")
        return None

def delete_image(filename, folder):
    """
    Supprime une image
    
    Args:
        filename: Nom du fichier à supprimer
        folder: Dossier contenant l'image
    
    Returns:
        bool: True si succès, False si erreur
    """
    try:
        if not filename:
            return False

        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
            
        return False

    except Exception as e:
        current_app.logger.error(f"Erreur lors de la suppression de l'image: {str(e)}")
        return False

def get_image_url(filename, folder):
    """
    Retourne l'URL d'une image
    
    Args:
        filename: Nom du fichier
        folder: Dossier contenant l'image
    
    Returns:
        str: URL de l'image ou None si erreur
    """
    try:
        if not filename:
            return None

        return f"/uploads/{folder}/{filename}"

    except Exception as e:
        current_app.logger.error(f"Erreur lors de la génération de l'URL: {str(e)}")
        return None
