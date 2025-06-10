"""
Script pour générer des données de test pour Citrus Music Server
"""

import os
import sys
import random
import string
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Constantes pour la génération de données
TRACK_COUNT = 1000  # Nombre de pistes à générer
PLAYLIST_COUNT = 50  # Nombre de playlists à générer
MAX_TRACKS_PER_PLAYLIST = 100  # Nombre maximum de pistes par playlist
GENRES = ["Rock", "Pop", "Jazz", "Classical", "Electronic", "Hip-Hop", "R&B", "Country", "Metal", "Folk"]
YEARS = list(range(1950, 2025))

def create_app():
    """Crée une application Flask pour le test"""
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///instance/citrus.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY='dev-key-for-testing'
    )
    
    # Initialiser la base de données
    from src.database import db
    db.init_app(app)
    
    return app

def generate_random_string(length=10):
    """Génère une chaîne aléatoire de caractères"""
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

def generate_random_title():
    """Génère un titre de piste aléatoire"""
    words = ["Love", "Heart", "Dream", "Night", "Day", "Life", "Time", "Road", "Sky", "Sun", 
             "Moon", "Star", "Fire", "Water", "Earth", "Wind", "Soul", "Mind", "Body", "Spirit"]
    
    title_length = random.randint(1, 3)
    return ' '.join(random.choice(words) for _ in range(title_length))

def generate_random_artist():
    """Génère un nom d'artiste aléatoire"""
    first_names = ["John", "Michael", "David", "James", "Robert", "Mary", "Jennifer", "Linda", 
                   "Elizabeth", "Susan", "The", "DJ", "MC", "Dr.", "Little", "Big"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson",
                  "Moore", "Taylor", "Band", "Orchestra", "Quartet", "Trio", "Brothers", "Sisters"]
    
    if random.random() < 0.3:  # 30% de chance d'avoir un nom simple
        return random.choice(first_names)
    elif random.random() < 0.7:  # 40% de chance d'avoir un nom complet
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    else:  # 30% de chance d'avoir un nom de groupe
        return f"The {generate_random_string(5)} {random.choice(['Band', 'Crew', 'Ensemble', 'Project'])}"

def generate_random_album():
    """Génère un nom d'album aléatoire"""
    adjectives = ["Dark", "Bright", "Silent", "Loud", "Eternal", "Temporary", "Lost", "Found", 
                  "Hidden", "Revealed", "Broken", "Mended", "Wild", "Tame", "Sweet", "Bitter"]
    nouns = ["Symphony", "Rhapsody", "Journey", "Adventure", "Story", "Tale", "Dream", "Nightmare",
             "Memory", "Vision", "Echo", "Reflection", "Shadow", "Light", "Whisper", "Scream"]
    
    if random.random() < 0.7:  # 70% de chance d'avoir un nom d'album standard
        return f"{random.choice(adjectives)} {random.choice(nouns)}"
    else:  # 30% de chance d'avoir un nom d'album plus complexe
        return f"The {random.choice(adjectives)} {random.choice(nouns)} of {generate_random_string(7)}"

def generate_tracks(db_session, count=TRACK_COUNT):
    """Génère des pistes aléatoires"""
    from src.models.track import Track
    
    logger.info(f"Génération de {count} pistes...")
    tracks = []
    
    for i in range(count):
        # Calculer des valeurs aléatoires pour les propriétés audio
        duration = random.randint(60, 600)  # Entre 1 et 10 minutes
        file_size = random.randint(1000000, 20000000)  # Entre 1 et 20 Mo
        bitrate = random.choice([128, 192, 256, 320])  # Bitrates courants en kbps
        sample_rate = random.choice([44100, 48000, 96000])  # Fréquences d'échantillonnage courantes
        
        track = Track(
            title=generate_random_title(),
            artist=generate_random_artist(),
            album=generate_random_album(),
            duration=duration,
            file_path=f"music/{generate_random_string(10)}.mp3",
            file_size=file_size,
            bitrate=bitrate,
            sample_rate=sample_rate,
            created_at=datetime.now() - timedelta(days=random.randint(0, 365))
        )
        tracks.append(track)
        
        # Ajouter par lots pour éviter de surcharger la mémoire
        if len(tracks) >= 100:
            db_session.add_all(tracks)
            db_session.commit()
            tracks = []
            logger.info(f"  {i+1}/{count} pistes générées")
    
    # Ajouter les pistes restantes
    if tracks:
        db_session.add_all(tracks)
        db_session.commit()
    
    logger.info(f"Génération de {count} pistes terminée")

def check_user_table_structure(db_session):
    """Vérifie la structure de la table users pour s'assurer que la colonne is_admin existe"""
    from sqlalchemy import inspect
    
    inspector = inspect(db_session.bind)
    columns = [column['name'] for column in inspector.get_columns('users')]
    
    logger.info(f"Colonnes de la table users: {columns}")
    
    # Vérifier si la colonne is_admin existe
    has_is_admin = 'is_admin' in columns
    logger.info(f"La colonne is_admin existe: {has_is_admin}")
    
    return has_is_admin

def generate_playlists(db_session, count=PLAYLIST_COUNT):
    """Génère des playlists aléatoires"""
    from src.models.playlist import Playlist
    from src.models.track import Track
    from src.models.user import User
    from sqlalchemy import text
    
    # Vérifier la structure de la table users
    has_is_admin = check_user_table_structure(db_session)
    
    # Récupérer les utilisateurs
    if has_is_admin:
        users = db_session.query(User).all()
    else:
        # Utiliser une requête SQL brute pour éviter l'erreur de colonne manquante
        result = db_session.execute(text("SELECT id, username, email FROM users"))
        users = [{'id': row[0], 'username': row[1], 'email': row[2]} for row in result]
    
    if not users:
        logger.error("Aucun utilisateur trouvé. Impossible de générer des playlists.")
        return
    
    # Récupérer les pistes
    track_ids = [track_id for (track_id,) in db_session.query(Track.id).all()]
    if not track_ids:
        logger.error("Aucune piste trouvée. Impossible de générer des playlists.")
        return
    
    logger.info(f"Génération de {count} playlists...")
    
    for i in range(count):
        # Choisir un utilisateur aléatoire
        user = random.choice(users)
        
        # Créer une playlist
        playlist = Playlist(
            name=f"Playlist {generate_random_string(8)}",
            description=f"Une playlist générée automatiquement avec {random.randint(5, MAX_TRACKS_PER_PLAYLIST)} pistes",
            user_id=user['id'] if isinstance(user, dict) else user.id,
            created_at=datetime.now() - timedelta(days=random.randint(0, 180))
        )
        db_session.add(playlist)
        db_session.flush()  # Pour obtenir l'ID de la playlist
        
        # Ajouter des pistes à la playlist
        track_count = random.randint(5, min(MAX_TRACKS_PER_PLAYLIST, len(track_ids)))
        playlist_tracks = random.sample(track_ids, track_count)
        
        for position, track_id in enumerate(playlist_tracks):
            db_session.execute(
                text("INSERT INTO playlist_tracks (playlist_id, track_id, position) VALUES (:playlist_id, :track_id, :position)"),
                {"playlist_id": playlist.id, "track_id": track_id, "position": position}
            )
        
        # Valider les changements
        db_session.commit()
        
        if (i + 1) % 10 == 0:
            logger.info(f"  {i+1}/{count} playlists générées")
    
    logger.info(f"Génération de {count} playlists terminée")

def create_users_if_needed(db_session):
    """Crée des utilisateurs si aucun n'existe"""
    from sqlalchemy import text, func
    
    # Vérifier s'il y a des utilisateurs en utilisant une requête SQL brute
    result = db_session.execute(text("SELECT COUNT(*) FROM users"))
    user_count = result.scalar()
    
    if user_count == 0:
        logger.info("Aucun utilisateur trouvé. Création d'utilisateurs de test...")
        
        # Créer quelques utilisateurs de test avec une requête SQL brute
        for i in range(1, 4):  # Créer 3 utilisateurs
            username = f"user{i}"
            email = f"user{i}@example.com"
            password_hash = "pbkdf2:sha256:150000$" + generate_random_string(20)
            created_at = datetime.now().isoformat()
            
            # Insérer l'utilisateur sans utiliser la colonne is_admin
            db_session.execute(
                text("INSERT INTO users (username, email, password_hash, created_at) VALUES (:username, :email, :password_hash, :created_at)"),
                {"username": username, "email": email, "password_hash": password_hash, "created_at": created_at}
            )
        
        db_session.commit()
        logger.info("Création de 3 utilisateurs terminée")

def main():
    """Fonction principale"""
    logger.info("Démarrage de la génération de données de test...")
    
    # Créer l'application Flask
    app = create_app()
    
    # Générer les données
    with app.app_context():
        from src.database import db_session
        
        try:
            # Créer des utilisateurs si nécessaire
            create_users_if_needed(db_session)
            
            # Générer des pistes
            generate_tracks(db_session)
            
            # Générer des playlists
            generate_playlists(db_session)
            
            logger.info("Génération de données de test terminée avec succès")
            
        except SQLAlchemyError as e:
            logger.error(f"Erreur lors de la génération des données : {str(e)}")
            db_session.rollback()
        finally:
            db_session.close()

if __name__ == "__main__":
    main()
