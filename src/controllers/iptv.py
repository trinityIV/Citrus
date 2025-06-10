from fastapi import APIRouter
from fastapi.responses import JSONResponse
from services.iptv_scraper import IPTVScraper

router = APIRouter()
scraper = IPTVScraper()

@router.get("/api/iptv")
async def get_iptv():
    streams = await scraper.get_streams()
    # Format enrichi pour le frontend (logo, pays, langue, catégorie)
    channels = []
    for s in streams:
        channels.append({
            'id': s.get('id'),
            'name': s.get('name'),
            'url': s.get('url'),
            'logo': s.get('logo', ''),
            'country': s.get('country', ''),
            'language': s.get('language', ''),
            'category': s.get('category', ''),
        })
    return JSONResponse({"channels": channels})
