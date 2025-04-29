from fastapi import FastAPI
from app.api.routes import video_edit

app = FastAPI(
    title="ClipCatch API",
    version="2.0.3"
)

app.include_router(video_edit.router, prefix="/api/video", tags=["Video Editor"])
