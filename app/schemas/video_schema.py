from pydantic import BaseModel

class VideoEditResponse(BaseModel):
    status: str
    output_video_path: str
