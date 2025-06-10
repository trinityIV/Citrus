#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de génération de données de test pour Citrus Music Server
Génère 1000 pistes musicales, 50 playlists et les associations entre eux
"""

import os
import sys
import random
import string
import datetime
from faker import Faker

# Ajouter le répertoire parent au path pour pouvoir importer les modules du projet
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, Track, Playlist, PlaylistTrack, User

# Configuration
NUM_TRACKS = 1000
NUM_PLAYLISTS = 50
MIN_TRACKS_PER_PLAYLIST = 5
MAX_TRACKS_PER_PLAYLIST = 100

# Initialisation de Faker pour générer des données aléatoires
fake = Faker()

# Listes pour générer des données musicales réalistes
genres = [
    "Rock", "Pop", "Hip Hop", "Rap", "Jazz", "Blues", "Classical", "Electronic",
    "Dance", "R&B", "Soul", "Country", "Folk", "Metal", "Punk", "Reggae",
    "Indie", "Alternative", "Disco", "Funk", "Techno", "House", "Ambient",
    "Trance", "Drum & Bass", "Dubstep", "Gospel", "Latin", "World"
]

def generate_duration():
    """Génère une durée aléatoire entre 2 et 8 minutes"""
    return random.randint(120, 480)

def generate_file_path(artist, title):
    """Génère un chemin de fichier pour une piste"""
    safe_artist = "".join(c for c in artist if c.isalnum() or c in " -_").strip()
    safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
    filename = f"{safe_artist} - {safe_title}.mp3"
    return os.path.join("uploads", "music", filename)

def generate_tracks(count):
    """Génère des pistes musicales aléatoires"""
    tracks = []
    
    print(f"Génération de {count} pistes musicales...")
    
    for i in range(count):
        artist = fake.name()
        title = " ".join(fake.words(nb=random.randint(1, 5))).title()
        album = " ".join(fake.words(nb=random.randint(1, 4))).title()
        genre = random.choice(genres)
        duration = generate_duration()
        file_path = generate_file_path(artist, title)
        year = random.randint(1960, 2025)
        
        track = Track(
            title=title,
            artist=artist,
            album=album,
            genre=genre,
            duration=duration,
            file_path=file_path,
            year=year,
            created_at=fake.date_time_between(start_date="-1y", end_date="now")
        )
        tracks.append(track)
        
        if (i + 1) % 100 == 0:
            print(f"  {i + 1} pistes générées...")
    
    return tracks

def generate_playlists(count, users):
    """Génère des playlists aléatoires associées aux utilisateurs"""
    playlists = []
    
    print(f"Génération de {count} playlists...")
    
    for i in range(count):
        name = fake.catch_phrase()
        description = fake.text(max_nb_chars=200)
        user = random.choice(users)
        
        playlist = Playlist(
            name=name,
            description=description,
            user_id=user.id,
            created_at=fake.date_time_between(start_date="-1y", end_date="now"),
            updated_at=fake.date_time_between(start_date="-1m", end_date="now")
        )
        playlists.append(playlist)
    
    return playlists

def associate_tracks_to_playlists(playlists, tracks):
    """Associe un nombre aléatoire de pistes à chaque playlist"""
    associations = []
    
    print("Association des pistes aux playlists...")
    
    for playlist in playlists:
        # Déterminer combien de pistes ajouter à cette playlist
        num_tracks = random.randint(MIN_TRACKS_PER_PLAYLIST, MAX_TRACKS_PER_PLAYLIST)
        # Sélectionner des pistes aléatoires
        playlist_tracks = random.sample(tracks, num_tracks)
        
        for i, track in enumerate(playlist_tracks):
            association = PlaylistTrack(
                playlist_id=playlist.id,
                track_id=track.id,
                position=i
            )
            associations.append(association)
        
        print(f"  Playlist '{playlist.name}': {num_tracks} pistes ajoutées")
    
    return associations

def main():
    """Fonction principale pour générer les données de test"""
    app = create_app()
    
    with app.app_context():
        print("Démarrage de la génération de données de test...")
        
        # Récupérer les utilisateurs existants
        users = User.query.all()
        if not users:
            print("ERREUR: Aucun utilisateur trouvé. Veuillez créer au moins un utilisateur avant d'exécuter ce script.")
            return
        
        # Générer les pistes
        tracks = generate_tracks(NUM_TRACKS)
        
        # Ajouter les pistes à la base de données
        print("Ajout des pistes à la base de données...")
        db.session.add_all(tracks)
        db.session.commit()
        
        # Générer les playlists
        playlists = generate_playlists(NUM_PLAYLISTS, users)
        
        # Ajouter les playlists à la base de données
        print("Ajout des playlists à la base de données...")
        db.session.add_all(playlists)
        db.session.commit()
        
        # Associer les pistes aux playlists
        associations = associate_tracks_to_playlists(playlists, tracks)
        
        # Ajouter les associations à la base de données
        print("Ajout des associations playlist-piste à la base de données...")
        db.session.add_all(associations)
        db.session.commit()
        
        print("\nGénération de données de test terminée avec succès!")
        print(f"  {len(tracks)} pistes générées")
        print(f"  {len(playlists)} playlists générées")
        print(f"  {len(associations)} associations playlist-piste créées")

if __name__ == "__main__":
    main()
