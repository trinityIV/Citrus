# Guide de Test Citrus Music Server

## 1. Configuration de l'Environnement

### 1.1 Prérequis Système
- Python 3.13
- FFmpeg pour la conversion média
- Libtorrent pour le streaming torrent
- Base de données SQLite

### 1.2 Installation des Dépendances
```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 1.3 Configuration de la Base de Données
```bash
# Définir la variable d'environnement
set FLASK_APP=src

# Initialiser la base de données
flask db upgrade
```

## 2. Test des Fonctionnalités

### 2.1 Gestion des Utilisateurs
- [ ] Créer un nouvel utilisateur
- [ ] Se connecter
- [ ] Modifier le profil
- [ ] Tester les permissions

### 2.2 Gestion des Playlists
- [ ] Créer une nouvelle playlist
- [ ] Ajouter des pistes
- [ ] Réorganiser l'ordre des pistes
- [ ] Supprimer des pistes
- [ ] Supprimer une playlist
- [ ] Partager une playlist

### 2.3 Bibliothèque Musicale
- [ ] Importer des fichiers audio
- [ ] Scanner un dossier pour les médias
- [ ] Éditer les métadonnées
- [ ] Rechercher des pistes
- [ ] Filtrer par genre/artiste/album
- [ ] Trier les résultats

### 2.4 Lecture Audio
- [ ] Lecture/Pause
- [ ] Navigation dans la piste
- [ ] Contrôle du volume
- [ ] Mode répétition
- [ ] Mode aléatoire
- [ ] File d'attente de lecture
- [ ] Crossfade entre les pistes

### 2.5 Streaming et Téléchargement
- [ ] Streaming IPTV
  - [ ] Ajouter une source IPTV
  - [ ] Charger la liste des chaînes
  - [ ] Lire un flux
  - [ ] Enregistrer un flux

- [ ] Streaming Torrent
  - [ ] Ajouter un torrent
  - [ ] Gérer la file d'attente
  - [ ] Contrôler la bande passante
  - [ ] Vérifier les seeds/peers

- [ ] Téléchargement
  - [ ] YouTube/SoundCloud
  - [ ] Spotify
  - [ ] Autres sources

### 2.6 Conversion Média
- [ ] Convertir en MP3
- [ ] Convertir en WAV
- [ ] Convertir en FLAC
- [ ] Extraire l'audio d'une vidéo
- [ ] Gérer les sous-titres
- [ ] Vérifier la qualité de conversion

### 2.7 Interface Utilisateur
- [ ] Responsive design
- [ ] Thème sombre/clair
- [ ] Animations fluides
- [ ] Menu mobile
- [ ] Notifications
- [ ] Glisser-déposer
- [ ] Raccourcis clavier

### 2.8 Performance
- [ ] Temps de chargement initial
- [ ] Réactivité de l'interface
- [ ] Utilisation mémoire
- [ ] Charge CPU
- [ ] Bande passante réseau

## 3. Tests Spécifiques Raspberry Pi

### 3.1 Optimisations
- [ ] Vérifier la charge CPU
- [ ] Monitorer la température
- [ ] Ajuster la qualité du streaming
- [ ] Optimiser la mise en cache

### 3.2 Configuration Réseau
- [ ] Configuration WiFi
- [ ] Port forwarding
- [ ] DLNA/UPnP
- [ ] Accès distant sécurisé

### 3.3 Stockage
- [ ] Gestion du stockage externe
- [ ] Montage automatique
- [ ] Sauvegarde des données
- [ ] Nettoyage du cache

## 4. Résolution des Problèmes Courants

### 4.1 Logs à Vérifier
- `/var/log/citrus/app.log`
- `/var/log/citrus/error.log`
- `/var/log/citrus/access.log`

### 4.2 Points de Vérification
- Permissions des fichiers
- Configuration FFmpeg
- Configuration Libtorrent
- Connexion base de données
- Cache navigateur
- Certificats SSL

## 5. Commandes Utiles

### 5.1 Gestion du Service
```bash
# Démarrer le serveur
flask run

# Avec rechargement automatique
FLASK_ENV=development flask run

# Avec accès externe
flask run --host=0.0.0.0
```

### 5.2 Base de Données
```bash
# Créer une nouvelle migration
flask db migrate -m "Description"

# Appliquer les migrations
flask db upgrade

# Retourner à une version précédente
flask db downgrade
```

### 5.3 Maintenance
```bash
# Nettoyer le cache
flask clean-cache

# Vérifier l'intégrité de la base
flask db-check

# Optimiser la base
flask db-optimize
```

## 6. Notes de Sécurité
- Toujours utiliser HTTPS en production
- Configurer un pare-feu
- Mettre à jour régulièrement les dépendances
- Sauvegarder régulièrement la base de données
- Ne pas exposer les logs en production
- Utiliser des clés API sécurisées
- Configurer les en-têtes de sécurité
