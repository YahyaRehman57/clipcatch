import requests
from typing import List
from app.schemas.video_schema import VideoEditRequest


class VideoCropService:

    def download_and_validate_video(cls, video_url: str):...


    @classmethod
    def crop_video(cls, request: VideoEditRequest) -> List[str]:
        video_path = cls.download_and_validate_video(request.video_url)