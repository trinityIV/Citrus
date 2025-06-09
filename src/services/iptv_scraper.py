"""
Service de scraping IPTV.
Récupère et agrège les flux depuis diverses sources gratuites.
"""

import asyncio
import aiohttp
import m3u8
import logging
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class IPTVScraper:
    """Scraper pour flux IPTV gratuits (scrapping only, aucune clé/API externe)"""
    
    def __init__(self):
        # Sources de base (m3u/m3u8)
        self.base_sources = [
            'https://iptv-org.github.io/iptv/index.m3u',
            'https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8',
            'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/fr.m3u',  # France
            'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/us.m3u',  # USA
            'https://raw.githubusercontent.com/iptv-org/iptv/master/streams/uk.m3u',  # UK
        ]
        
        # Sites à scraper
        self.scrape_sources = [
            {
                'url': 'https://www.stream-live.tv/',
                'selector': '.channel-list .channel-item',
                'name_selector': '.channel-name',
                'stream_selector': 'data-stream'
            },
            {
                'url': 'https://123tv.live/',
                'selector': '.channel-grid .channel',
                'name_selector': '.channel-name',
                'stream_selector': 'data-url'
            }
        ]
        
        # Cache des flux (TTL: 1 heure)
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = 3600  # secondes
        self.last_update = None
    
    async def get_streams(self, force_update: bool = False) -> List[Dict[str, Any]]:
        """
        Récupère tous les flux disponibles.
        
        Args:
            force_update: Force la mise à jour du cache
            
        Returns:
            Liste des flux disponibles
        """
        # Vérifier le cache
        if not force_update and self.cache and self.last_update:
            if (datetime.now() - self.last_update).total_seconds() < self.cache_ttl:
                return list(self.cache.values())
        
        # Récupérer les flux depuis toutes les sources
        streams = []
        async with aiohttp.ClientSession() as session:
            # 1. Récupérer les playlists M3U
            m3u_tasks = [
                self._fetch_m3u(session, url)
                for url in self.base_sources
            ]
            m3u_results = await asyncio.gather(*m3u_tasks, return_exceptions=True)
            
            for result in m3u_results:
                if isinstance(result, list):
                    streams.extend(result)
            
            # 2. Scraper les sites web
            scrape_tasks = [
                self._scrape_site(session, source)
                for source in self.scrape_sources
            ]
            scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)
            
            for result in scrape_results:
                if isinstance(result, list):
                    streams.extend(result)
        
        # Mettre à jour le cache
        self.cache = {
            stream['id']: stream
            for stream in streams
        }
        self.last_update = datetime.now()
        
        return streams
    
    async def _fetch_m3u(self, session: aiohttp.ClientSession, url: str) -> List[Dict[str, Any]]:
        """Récupère et parse une playlist M3U"""
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Erreur lors de la récupération de {url}: {response.status}")
                    return []
                
                content = await response.text()
                playlist = m3u8.loads(content)
                
                streams = []
                for segment in playlist.segments:
                    stream = {
                        'id': f"{url}_{len(streams)}",
                        'name': segment.title or f"Stream {len(streams)}",
                        'url': segment.uri,
                        'source': url,
                        'type': 'live',
                        'format': self._detect_format(segment.uri),
                        'added': datetime.now().isoformat()
                    }
                    streams.append(stream)
                
                return streams
                
        except Exception as e:
            logger.error(f"Erreur lors du parsing de {url}: {str(e)}")
            return []
    
    async def _scrape_site(self, session: aiohttp.ClientSession, source: Dict) -> List[Dict[str, Any]]:
        """Scrape un site web pour trouver des flux"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with session.get(source['url'], headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Erreur lors du scraping de {source['url']}: {response.status}")
                    return []
                
                # Parser le HTML
                from bs4 import BeautifulSoup
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                streams = []
                for item in soup.select(source['selector']):
                    try:
                        name = item.select_one(source['name_selector']).text.strip()
                        stream_url = item.get(source['stream_selector'])
                        
                        if stream_url:
                            if not stream_url.startswith('http'):
                                stream_url = urljoin(source['url'], stream_url)
                            
                            stream = {
                                'id': f"{source['url']}_{len(streams)}",
                                'name': name,
                                'url': stream_url,
                                'source': source['url'],
                                'type': 'live',
                                'format': self._detect_format(stream_url),
                                'added': datetime.now().isoformat()
                            }
                            streams.append(stream)
                            
                    except Exception as e:
                        logger.error(f"Erreur lors du parsing d'un élément: {str(e)}")
                        continue
                
                return streams
                
        except Exception as e:
            logger.error(f"Erreur lors du scraping de {source['url']}: {str(e)}")
            return []
    
    def _detect_format(self, url: str) -> str:
        """Détecte le format du flux basé sur l'URL"""
        url = url.lower()
        if '.m3u8' in url:
            return 'hls'
        elif '.mpd' in url:
            return 'dash'
        elif '.mp4' in url:
            return 'mp4'
        elif '.ts' in url:
            return 'ts'
        else:
            return 'unknown'
    
    async def check_stream(self, url: str) -> bool:
        """Vérifie si un flux est accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=5) as response:
                    return response.status == 200
        except:
            return False
