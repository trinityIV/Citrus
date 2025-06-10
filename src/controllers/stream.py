from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import JSONResponse
import subprocess
import tempfile
import os

router = APIRouter()

@router.post("/api/stream/magnet")
async def stream_magnet(request: Request, torrent: UploadFile = File(None)):
    data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else None
    magnet = data.get("magnet") if data else None
    temp_torrent = None
    if not magnet and torrent:
        # Save uploaded .torrent file to temp and build file path
        temp_dir = tempfile.mkdtemp()
        temp_torrent = os.path.join(temp_dir, torrent.filename)
        with open(temp_torrent, "wb") as f:
            f.write(await torrent.read())
    # Launch peerflix/webtorrent-hybrid to stream (assumes installed globally)
    # Choose a random port to avoid collisions
    import random
    port = random.randint(40000, 49999)
    if magnet:
        cmd = f"peerflix '{magnet}' --port {port} --vlc --list --path /tmp --no-quit --on-error exit"
    elif temp_torrent:
        cmd = f"peerflix '{temp_torrent}' --port {port} --vlc --list --path /tmp --no-quit --on-error exit"
    else:
        return JSONResponse({"error": "Aucun lien magnet ou fichier torrent fourni."}, status_code=400)
    # Start peerflix as a subprocess (non-bloquant)
    subprocess.Popen(cmd, shell=True)
    stream_url = f"http://localhost:{port}"
    return JSONResponse({"stream_url": stream_url})
