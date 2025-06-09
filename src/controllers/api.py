"""
Contrôleur principal de l'API Citrus Music.
Gère les endpoints pour la recherche, les playlists et les téléchargements.
"""

import asyncio
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from services.search import SearchService
from services.playlist import PlaylistService
from services.download import DownloadManager
from utils.exceptions import (
    ServiceError,
    DownloadError,
    ValidationError,
    AuthenticationError
)

# Créer le routeur FastAPI
router = APIRouter(prefix="/api")

# Modèles de données
class SearchQuery(BaseModel):
    q: str
    limit: Optional[int] = 20
    sources: Optional[List[str]] = None

class PlaylistQuery(BaseModel):
    url: str

class TrackDownload(BaseModel):
    url: str
    source: str
    title: str
    artist: Optional[str] = None

class BatchDownload(BaseModel):
    tracks: List[TrackDownload]
    playlist_id: Optional[str] = None
    playlist_title: Optional[str] = None

# Services
search_service = SearchService()
playlist_service = PlaylistService()
download_manager = DownloadManager()

@router.post("/search")
async def search_tracks(query: SearchQuery):
    """
    Recherche des pistes sur toutes les plateformes configurées.
    """
    try:
        results = await search_service.search(
            query=query.q,
            limit=query.limit,
            sources=query.sources
        )
        return results
        
    except ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.post("/playlist")
async def get_playlist_info(query: PlaylistQuery):
    """
    Récupère les informations d'une playlist à partir de son URL.
    """
    try:
        playlist = await playlist_service.get_playlist_info(query.url)
        return playlist
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.post("/download")
async def download_track(track: TrackDownload, background_tasks: BackgroundTasks):
    """
    Lance le téléchargement d'une piste en arrière-plan.
    """
    try:
        # Valider la piste
        if not track.url or not track.source or not track.title:
            raise ValidationError("URL, source et titre sont requis")
            
        # Ajouter à la file d'attente
        download_id = await download_manager.add_to_queue(track)
        
        # Démarrer le téléchargement en arrière-plan
        background_tasks.add_task(
            download_manager.process_download,
            download_id
        )
        
        return {"status": "success", "download_id": download_id}
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.post("/downloads/batch")
async def batch_download(batch: BatchDownload, background_tasks: BackgroundTasks):
    """
    Lance le téléchargement d'un lot de pistes en arrière-plan.
    """
    try:
        # Valider le lot
        if not batch.tracks:
            raise ValidationError("La liste des pistes est vide")
            
        # Créer un identifiant de lot
        batch_id = await download_manager.create_batch(
            tracks=batch.tracks,
            playlist_id=batch.playlist_id,
            playlist_title=batch.playlist_title
        )
        
        # Démarrer le traitement en arrière-plan
        background_tasks.add_task(
            download_manager.process_batch,
            batch_id
        )
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "total_tracks": len(batch.tracks)
        }
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DownloadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.get("/downloads/{download_id}/status")
async def get_download_status(download_id: str):
    """
    Récupère le statut d'un téléchargement.
    """
    try:
        status = await download_manager.get_status(download_id)
        return status
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.get("/downloads/batch/{batch_id}/status")
async def get_batch_status(batch_id: str):
    """
    Récupère le statut d'un lot de téléchargements.
    """
    try:
        status = await download_manager.get_batch_status(batch_id)
        return status
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")
