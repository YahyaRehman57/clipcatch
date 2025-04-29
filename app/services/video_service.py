import shutil
import requests
import os, uuid
from app.schemas.video_schema import VideoEditRequest, WebhookVideo, WebhookVideoResponse
from pathlib import Path
import ffmpeg
from app import ErrorResponse
from typing import Any, List
from app.config.logger import LogManager
from datetime import datetime
from app.core.exceptions import CustomError

class VideoService:
    MEDIA_ROOT = Path("media")
    LOGGER = LogManager.get_logger("video_service")

    @classmethod
    def create_media_folder(cls):
        unique_id = str(uuid.uuid4())
        current_date = datetime.now().strftime('%Y-%m-%d')
        unique_folder = os.path.join(cls.MEDIA_ROOT, current_date, unique_id)
        os.makedirs(unique_folder, exist_ok=True)
        return unique_folder



    @classmethod
    def validate_and_download(cls, folder: str, video_url: str) -> str:
        # 1. Validate URL
        if not video_url.lower().startswith(('http://', 'https://')):
            cls.LOGGER.info(f"Invalid video URL provided.")
            raise ValueError("Invalid video URL provided.")
        
        # 3. Download the video
        video_path = f"{folder}\input_video.mp4"
        try:
            response = requests.get(video_url, stream=True, timeout=15)
            response.raise_for_status()
            with open(video_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
        except requests.RequestException as e:
            shutil.rmtree(folder)
            cls.LOGGER.info(f"Failed to download video {e}.")
            raise ValueError("Failed to download video.")

        # 4. Use ffmpeg-python to get duration
        try:
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe['format']['duration'])
            duration_minutes = duration / 60.0
            cls.LOGGER.info(f"Video duration {duration_minutes}")

            if duration_minutes < 1 or duration_minutes > 7:
                shutil.rmtree(folder)
                cls.LOGGER.info("Video duration must be between 1 and 7 minutes.")
                raise ValueError("Video duration must be between 1 and 7 minutes.")

        except Exception as e:
            shutil.rmtree(folder)
            cls.LOGGER.info(f"Error reading video metadata: {e}")
            raise ValueError("Error reading video metadata.")

        return str(video_path)

    @classmethod
    def handle_edit(cls, request: VideoEditRequest):
        try:
            cls.LOGGER.info(f"Incoming request is : {request.model_dump()}")
            media_foler = cls.create_media_folder()
            cls.LOGGER.info(f"Media folder is  : {media_foler}")
            if media_foler:
                video_path = cls.validate_and_download(media_foler, request.video_url)

        except ValueError as e:
            return cls.call_webhook(
                request=request,
                status_code=400,
                message=str(e)
            )
        
    @classmethod
    def call_webhook(
        cls,
        request: VideoEditRequest,
        status_code: int,
        message: str,
        data: List[WebhookVideo] = []
    ):
        cls.LOGGER.info("Preparing to send webhook callback.")
        webhook_url = request.webhook_url
        metadata = request.metadata

        cls.LOGGER.debug(f"Webhook URL: {webhook_url}")
        cls.LOGGER.debug(f"Metadata: {metadata}")
        cls.LOGGER.debug(f"Status code: {status_code}, Message: {message}, Data: {data}")

        # Build the webhook response body
        webhook_body = WebhookVideoResponse(
            message=message,
            status_code=status_code,
            videos=data if data else None,
            metadata=metadata
        ).model_dump()

        try:
            cls.LOGGER.info(f"Sending webhook to {webhook_url} with payload: {webhook_body}")
            response = requests.post(webhook_url, json=webhook_body, timeout=10)
            cls.LOGGER.info(
                f"Webhook sent. Status code: {response.status_code}, Response: {response.text}"
            )
        except requests.RequestException as e:
            cls.LOGGER.error(f"Failed to send webhook to {webhook_url}: {str(e)}")
        
