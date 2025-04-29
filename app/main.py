from fastapi import FastAPI, HTTPException
# from app.api.routes import video_edit
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

clipcatch_app = FastAPI(
    title="ClipCatch API",
    version="2.0.3"
)
MEDIA_DIR = Path("media")

# clipcatch_app.include_router(video_edit.router, prefix="/api/video", tags=["Video Editor"])


@clipcatch_app.get("/media/{folder}/{filename}")
def get_media_file(folder: str, filename: str):
    file_path = MEDIA_DIR / folder / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(path=file_path)


@clipcatch_app.post("/webhook")
def webhook(data):
    print("data is : ", data)
    return JSONResponse(status_code=200)