import os
from fastapi import FastAPI
from app.api.routes import video_edit
from fastapi.responses import JSONResponse
from pathlib import Path
from fastapi.staticfiles import StaticFiles


clipcatch_app = FastAPI(
    title="ClipCatch API",
    version="2.0.3"
)
MEDIA_DIR = Path("media")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MEDIA_DIR = Path(BASE_DIR) / "media"
FONTS_DIR = Path(BASE_DIR) / "static" / "fonts"

# Ensure directories exist
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)

clipcatch_app.include_router(video_edit.router, prefix="/api/video", tags=["Video Editor"])
clipcatch_app.mount("/fonts", StaticFiles(directory="static/fonts"), name="fonts")
clipcatch_app.mount("/media", StaticFiles(directory="media"), name="media")



@clipcatch_app.post("/webhook")
def webhook(data):
    print("data is : ", data)
    return JSONResponse(status_code=200)