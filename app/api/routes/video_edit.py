# from fastapi import APIRouter, UploadFile, File, BackgroundTasks
# from app.schemas.video_schema import VideoEditResponse, VideoEditRequest
# from app.services.video_service import VideoService
# from app import ErrorResponse, SuccessResponse
# from fastapi.responses import JSONResponse
# from typing import Union

# router = APIRouter()

# @router.post("/edit", response_model=Union[SuccessResponse, ErrorResponse])
# async def edit_video(request: VideoEditRequest, background_tasks: BackgroundTasks):
#     try:
#         print("request url : ", request.video_url)
#         background_tasks.add_task(VideoService.handle_edit, request)
#         response = SuccessResponse(message="Video editing has started and will be processed in the background.")
#         return JSONResponse(status_code=200, content=response.model_dump())
#     except Exception:
#         return JSONResponse(status_code=400, content=ErrorResponse(message="Unable to procede the request.").model_dump())


# # from fastapi import FastAPI, Depends
# # from sqlalchemy.orm import Session
# # from app.database import get_db
# # from sqlalchemy import text


# # @router.get("/test-db")
# # def test_database_connection(db: Session = Depends(get_db)):
# #     try:
# #         # Run a simple query
# #         result = db.execute(text("SELECT 1"))
# #         print("result is : ",result)
# #         return {"success": True, "message": "Database connected successfully!"}
# #     except Exception as e:
# #         return {"success": False, "error": str(e)}
