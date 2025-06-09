<div align="center">

# 🍊 Citrus Music Server

*Une solution de streaming musical moderne, élégante et performante*

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/trinityIV/Citrus/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%2FLinux-green)](https://www.raspberrypi.org/)
[![GitHub](https://img.shields.io/badge/GitHub-trinityIV%2FCitrus-black)](https://github.com/trinityIV/Citrus)

[Documentation](#documentation) • 
[Installation](#installation) • 
[Fonctionnalités](#fonctionnalités) • 
[Architecture](#architecture) • 
[Contribution](#contribution)

</div>

## 🌟 Vue d'ensemble

Citrus Music Server est une plateforme de streaming musical nouvelle génération, conçue pour offrir une expérience utilisateur exceptionnelle sur Raspberry Pi. Combinant une interface moderne avec des fonctionnalités avancées de streaming et de gestion de bibliothèque, Citrus représente l'avenir de la musique à domicile.

### Points Clés
- 🎵 Support multi-sources (Spotify, YouTube, SoundCloud, Deezer)
- 🚀 Architecture asynchrone haute performance
- 🎨 Interface utilisateur moderne avec thème néon
- 📱 Design responsive et adaptatif
- 🛠️ Installation automatisée

## ✨ Fonctionnalités

### Streaming et Lecture
- **Multi-Source** : Intégration transparente avec les principales plateformes de streaming
- **Format Universel** : Support de MP3, WAV, OGG, FLAC, et plus
- **IPTV** : Accès aux chaînes de radio en streaming
- **Conversion** : Transcodage à la volée pour une compatibilité optimale

### Gestion de Bibliothèque
- **Organisation** : Classement intelligent par artiste, album, genre
- **Métadonnées** : Édition avancée et récupération automatique
- **Playlists** : Création et gestion de listes de lecture
- **Pochettes** : Récupération automatique des artworks

### Performance
- **Asynchrone** : Architecture non-bloquante pour une réactivité maximale
- **Cache** : Système de mise en cache intelligent
- **Optimisé** : Conçu spécifiquement pour Raspberry Pi
- **Scalable** : Adapté aux bibliothèques de toutes tailles

## 🚀 Installation

### Installation Automatique (Recommandée)
```bash
# Cloner le dépôt
git clone https://github.com/trinityIV/Citrus.git
cd citrus

# Lancer l'installateur
chmod +x install.sh
./install.sh
```

### Installation Manuelle
```bash
# Prérequis système
sudo apt update && sudo apt install -y python3-pip ffmpeg

# Configuration Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Lancement
python src/web_app.py
```

## 🏗️ Architecture

### Backend
- **Flask** : Framework web léger et performant
- **aiohttp** : Clients API asynchrones
- **SQLAlchemy** : ORM pour la gestion des données
- **yt-dlp** : Téléchargement et streaming optimisés

### Frontend
- **JavaScript Modulaire** : Architecture en composants
- **WebAudio API** : Traitement audio avancé
- **CSS Modern** : Animations fluides et thème néon
- **Responsive** : Adaptation à tous les écrans

### Structure du Projet
```
citrus/
├── src/
│   ├── services/    # Services métier
│   ├── utils/       # Clients API et utilitaires
│   ├── routes/      # Routes de l'application
│   ├── static/      # Assets frontend
│   └── web_app.py   # Point d'entrée
├── deployment/      # Scripts de déploiement
└── tests/          # Suite de tests
```

## 📊 Performance

- **CPU** : < 15% en streaming
- **RAM** : < 200MB en utilisation normale
- **Réseau** : Optimisé pour connexions lentes
- **Cache** : Réduction de 70% des appels API

## 🤝 Contribution

Nous accueillons toutes les contributions ! Voici comment participer :

1. 🍴 Forker le projet
2. 🔧 Créer une branche (`git checkout -b feature/amelioration`)
3. 💾 Commiter les changements (`git commit -am 'Ajout feature'`)
4. 📤 Pusher la branche (`git push origin feature/amelioration`)
5. 📫 Ouvrir une Pull Request

## 📜 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- Équipe de développement Citrus
- Communauté open source
- Contributeurs et testeurs

---

<div align="center">
Créé avec ❤️ par trinityIV

[Documentation](https://github.com/trinityIV/Citrus/tree/main/docs) • [Issues](https://github.com/trinityIV/Citrus/issues) • [Discussions](https://github.com/trinityIV/Citrus/discussions)
</div>
