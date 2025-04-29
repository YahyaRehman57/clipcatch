from fastapi import APIRouter, UploadFile, File
from app.services.video_service import process_video
from app.schemas.video_schema import VideoEditResponse

router = APIRouter()

@router.post("/edit", response_model=VideoEditResponse)
async def edit_video(file: UploadFile = File(...)):
    output_path = await process_video(file)
    return VideoEditResponse(status="success", output_video_path=output_path)

# from fastapi import FastAPI, Depends
# from sqlalchemy.orm import Session
# from app.database import get_db
# from sqlalchemy import text


# @router.get("/test-db")
# def test_database_connection(db: Session = Depends(get_db)):
#     try:
#         # Run a simple query
#         result = db.execute(text("SELECT 1"))
#         print("result is : ",result)
#         return {"success": True, "message": "Database connected successfully!"}
#     except Exception as e:
#         return {"success": False, "error": str(e)}
