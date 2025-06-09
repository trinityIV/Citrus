<div align="center">

```
 ██████╗██╗████████╗██████╗ ██╗   ██╗███████╗
██╔════╝██║╚══██╔══╝██╔══██╗██║   ██║██╔════╝
██║     ██║   ██║   ██████╔╝██║   ██║███████╗
██║     ██║   ██║   ██╔══██╗██║   ██║╚════██║
╚██████╗██║   ██║   ██║  ██║╚██████╔╝███████║
 ╚═════╝╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
```

# 🍊 PATCHNOTE MAJEUR — Citrus devient 100% Scrapping Only !

</div>

---

## ✨ **Release Highlights**

> **Citrus Music Server** passe à une architecture **100% scrapping** : plus aucune clé API, plus aucune dépendance à des services externes, tout est basé sur yt-dlp et des sources publiques IPTV !

- 🚫 **Suppression totale des clients API (Spotify, YouTube, SoundCloud, Deezer)**
- ⚡ **yt-dlp** gère tous les téléchargements et extractions (musique, playlists)
- 🔓 **Plus aucune clé, token ou variable secrète requise**
- 📺 **IPTV 100% public** : M3U/M3U8 et parsing HTML uniquement
- 🛡️ **Sécurité et vie privée renforcées**
- 🥝 **Déploiement instantané sur Raspberry Pi**

---

## 🔄 **Avant / Après**

|               | **Avant** (API/clé) | **Après** (Scrapping only) |
|---------------|:-------------------:|:-------------------------:|
| YouTube       | API officielle      | yt-dlp                    |
| Spotify       | API + client_id     | yt-dlp                    |
| SoundCloud    | API + client_id     | yt-dlp                    |
| Deezer        | API (si utilisé)    | yt-dlp                    |
| IPTV          | APIs privées (rare) | M3U/M3U8 publics          |
| Backend       | Auth/clé/token      | 0 clé, 0 token            |
| Frontend      | Params API/clé      | Aucun paramètre secret    |

---

## 🛠️ **Ce qui a changé côté code**

- Suppression complète de tous les modules clients API et de leur logique
- Centralisation de tous les téléchargements sur yt-dlp (Python)
- Nettoyage de la config : plus aucune variable d’environnement sensible
- Refactoring backend et frontend pour ne dépendre que de scrapping public
- Ajout de helpers yt-dlp pour chaque source
- Vérification IPTV : tout est parsing public, aucun accès restreint
- Patchnotes et documentation mis à jour

---

## 🚀 **Pourquoi c’est une révolution ?**

- **Déploiement ultra-rapide** : clone, installe, lance, c’est prêt !
- **Aucune limite d’API** : jamais de quota, jamais de ban
- **Sécurité** : aucune fuite possible de clé ou de secret
- **Maintenance** : code plus simple, plus léger, plus durable
- **Respect de la vie privée** : tout est local, tout est open

---

## 📅 **Patch validé le 2025-06-10**

Pour toute question ou bug suite à cette migration, merci d’ouvrir une issue sur le dépôt ou de contacter le mainteneur.

---

<div align="center">

**🍊 Citrus — Le streaming libre, sans clé, pour tous !**

</div>

## Objectif
Refonte du backend Citrus pour garantir que tous les téléchargements de musiques, playlists et IPTV se font uniquement via du scrapping (yt-dlp, parsing M3U/M3U8/HTML public), sans aucune clé API, client_id, client_secret ou authentification externe.

---

## Modifications principales

### 1. Suppression des clients API et dépendances externes
- Suppression complète de la logique et des fichiers liés à :
  - `YouTubeClient` (`utils/youtube.py`)
  - `SoundCloudClient` (`utils/soundcloud.py`)
  - `SpotifyClient` (`utils/spotify.py`)
  - `MusicClients` et `get_music_clients` (`services/music_clients.py`)
- Ces modules sont remplacés par des helpers qui utilisent **yt-dlp** pour extraire les infos et télécharger musiques/playlists.

### 2. Centralisation des téléchargements sur yt-dlp
- Tous les téléchargements (tracks, playlists) passent désormais exclusivement par **yt-dlp** (API Python).
- Suppression de tout appel à des clients custom ou à des API officielles.
- Ajout d'un helper interne dans `services/download.py` pour gérer les téléchargements via yt-dlp, avec reporting de progression et gestion d'erreur.

### 3. Nettoyage de la configuration
- Suppression des variables d'environnement et options liées à des clés API (YOUTUBE_API_KEY, SOUNDCLOUD_CLIENT_ID, SPOTIFY_CLIENT_ID/SECRET).
- Conservation uniquement des options yt-dlp, des dossiers et des sources IPTV publiques.

### 4. IPTV : scrapping only
- Vérification que tout le scrapping IPTV (`iptv_scraper.py`, `stream_manager.py`) se fait uniquement via des listes publiques (M3U/M3U8) ou parsing HTML public, sans aucune clé ni API privée.
- Ajout de commentaires expliquant que tout est scrapping only.

### 5. Nettoyage du backend
- Suppression de toute référence à des clients API dans le backend.
- Mise à jour des endpoints Flask pour ne plus jamais exiger de clé API ou login externe.

---

## Conséquences
- Citrus est désormais 100% autonome pour le téléchargement de musiques, playlists et IPTV via scrapping, sans dépendance à des services tiers nécessitant une authentification.
- Plus aucune clé API ou variable secrète n'est nécessaire pour l'utilisation ou le déploiement.
- La maintenance et la portabilité du projet sont grandement facilitées.

---

## À faire côté frontend
- S'assurer que tous les appels AJAX/Fetch utilisent uniquement les nouveaux endpoints Flask (aucun besoin de clé API ou login externe).
- Adapter les notifications/messages utilisateur si une fonctionnalité dépendait d'une API supprimée.

---

**Patch validé le 2025-06-10**

Pour toute question ou bug suite à cette migration, merci d'ouvrir une issue sur le dépôt ou de contacter le mainteneur.
