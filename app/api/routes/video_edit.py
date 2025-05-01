from fastapi import APIRouter, BackgroundTasks
from app.schemas.video_schema import VideoEditRequest
from app.services.video_service import VideoService
from app import ErrorResponse, SuccessResponse
from fastapi.responses import JSONResponse
from typing import Union

router = APIRouter()

@router.post("/edit", response_model=Union[SuccessResponse, ErrorResponse])
async def edit_video(request: VideoEditRequest, background_tasks: BackgroundTasks):
    try:
        background_tasks.add_task(VideoService.handle_edit, request)
        response = SuccessResponse(message="Video editing has started and will be processed in the background.")
        return JSONResponse(status_code=200, content=response.model_dump())
    except Exception:
        return JSONResponse(status_code=400, content=ErrorResponse(message="Unable to procede the request.").model_dump())