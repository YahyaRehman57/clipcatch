import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from app.api.routes import video_edit
from fastapi.responses import JSONResponse
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from app.utils.file_opearations_utils import build_directory_tree

clipcatch_app = FastAPI(
    title="ClipCatch API",
    version="2.0.3"
)
MEDIA_DIR = Path("media")
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

MEDIA_DIR = Path(BASE_DIR) / "media"
FONTS_DIR = Path(BASE_DIR) / "static" / "fonts"
LOGS_DIR = Path(BASE_DIR) / "logs"

# Ensure directories exist
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


clipcatch_app.include_router(video_edit.router, prefix="/api/video", tags=["Video Editor"])
clipcatch_app.mount("/fonts", StaticFiles(directory="static/fonts"), name="fonts")
clipcatch_app.mount("/media", StaticFiles(directory="media"), name="media")




@clipcatch_app.get("/media-tree")
def get_media_tree():
    if MEDIA_DIR.exists():
        tree = build_directory_tree(MEDIA_DIR)
        return JSONResponse(content=tree)
    return JSONResponse(status_code=404, content={"error": "Media directory not found"})


@clipcatch_app.get("/logs-tree")
def get_logs_tree():
    if LOGS_DIR.exists():
        tree = build_directory_tree(LOGS_DIR)
        return JSONResponse(content=tree)
    return JSONResponse(status_code=404, content={"error": "Logs directory not found"})


@clipcatch_app.get("/download/{filename}", tags=["Logs"])
def download_log_file(filename: str):
    file_path = LOGS_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Log file not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@clipcatch_app.post("/webhook")
def webhook(data):
    print("data is : ", data)
    return JSONResponse(status_code=200)