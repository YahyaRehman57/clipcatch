import shutil
import requests
import os, uuid, cv2
from app.schemas.video_schema import VideoEditRequest, WebhookVideo, WebhookVideoResponse
from pathlib import Path
import ffmpeg
from app import ErrorResponse
from typing import Any, List, Dict
from app.config.logger import LogManager
from datetime import datetime
from app.core.config import VideoSettings
from .subtitle_service import SubtitleService
from .video_crop_service import VideoCropService
from .gemini_service import GeminiService
from app.schemas.ai_model import ColoredWord, AdvancedSRTResponse

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
        # video_path = f"{folder}\input_video.mp4"
        video_path = os.path.join(folder, VideoSettings.VIDEO_FILE)
        cls.LOGGER.info(f"Video path is : {video_path}")
        try:
            response = requests.get(video_url, stream=True, timeout=15)
            response.raise_for_status()
            with open(video_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
        except Exception as e:
            shutil.rmtree(folder)
            cls.LOGGER.info(f"Failed to download video {e}.")
            raise ValueError("Failed to download video.")

        # 4. Use ffmpeg-python to get duration
        try:
            cls.LOGGER.info("Getting video info...")
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frame_count / fps
            duration_minutes = duration / 60
            cap.release()

            #TODO
            if duration_minutes < 0.5 or duration_minutes > 7:
                shutil.rmtree(folder)
                cls.LOGGER.info("Video duration must be between 1 and 7 minutes.")
                raise ValueError("Video duration must be between 1 and 7 minutes.")
        except ValueError as e:
            cls.LOGGER.info(f"Error reading video metadata: {e}")
            raise e
        except Exception as e:
            shutil.rmtree(folder)
            cls.LOGGER.info(f"Error reading video metadata: {e}")
            raise ValueError("Error reading video metadata.")

        return str(video_path)

    @classmethod
    def get_srt_file_content(cls, srt_file_path: str) -> str:
        try:
            with open(srt_file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"File not found: {srt_file_path}")
            return ""
        except Exception as e:
            print(f"Error reading file {srt_file_path}: {e}")
            return ""

    @classmethod
    def handle_edit(cls, request: VideoEditRequest):
        try:
            cls.LOGGER.info(f"Incoming request: {request.model_dump()}")
            
            cls.LOGGER.info("Step 1: Creating media folder...")
            try:
                media_folder = cls.create_media_folder()
                cls.LOGGER.info(f"Media folder created successfully: {media_folder}")
            except Exception as e:
                cls.LOGGER.error(f"[Step 1] Failed to create media folder: {e}Video path is : {video_path}")
                return cls.call_webhook(
                    request=request,
                    status_code=400,
                    message=f"Unable to process the video. {1}"
                )

            cls.LOGGER.info("Step 2: Downloading video...")
            try:
                video_path = cls.validate_and_download(media_folder, request.video_url)
                cls.LOGGER.info(f"Video downloaded successfully at path: {video_path}")
            except Exception as e:
                cls.LOGGER.error(f"[Step 2] Video download failed: {e} Video path is : {video_path}")
                return cls.call_webhook(
                    request=request,
                    status_code=400,
                    message=f"Unable to process the video. {2}"
                )

            cls.LOGGER.info("Step 3: Generating initial SRT file...")
            try:
                srt_file = SubtitleService.generate_srt_file(request=request, folder=media_folder, video_path=video_path)
                cls.LOGGER.info(f"Generated initial SRT file: {srt_file}")
                if srt_file:
                    srt_content = cls.get_srt_file_content(srt_file_path=srt_file)
                    cls.LOGGER.debug(f"SRT Content (truncated): {srt_content[:300]}...")
                else:
                    raise ValueError("Unable to generate srt file")
            except Exception as e:
                cls.LOGGER.error(f"[Step 3] SRT generation failed: {e}, Video path is : {video_path}")
                return cls.call_webhook(
                    request=request,
                    status_code=400,
                    message=f"Unable to process the video. {3}"
                )

            cls.LOGGER.info("Step 4: Analyzing video for trimming or full-edit...")
            highlight_colors = request.highlight_colors or VideoSettings.HIGHLIGHT_COLORS
            highlighted_words: Dict[str, str] = {}
            aspect_ratios = request.aspect_ratios
            if not request.is_full_video_edit:
                cls.LOGGER.info("Trimming is required.")
                response = GeminiService().analyze_srt_advanced(srt_content=srt_content, color_list=highlight_colors)
                if isinstance(response, AdvancedSRTResponse):
                    range = response.active_speech_range
                    cls.LOGGER.info(f"Trimming video: {range.start_time} to {range.end_time}")
                    VideoCropService.trim_video(video_file_path=video_path, start_time_str=range.start_time, end_time_str=range.end_time)
                    words = response.colored_words
                    highlighted_words = {cw.word: cw.color for cw in words}
                    cls.LOGGER.debug(f"Highlighted words: {highlighted_words}")

                    cls.LOGGER.info("Regenerating SRT after trimming...")
                    try:
                        srt_file = SubtitleService.generate_srt_file(request=request, folder=media_folder, video_path=video_path)
                        cls.LOGGER.info(f"Regenerated SRT file: {srt_file}")
                        if srt_file:
                            srt_content = cls.get_srt_file_content(srt_file_path=srt_file)
                        else:
                            raise ValueError("Unable to generate srt file")
                    except Exception as e:
                        cls.LOGGER.error(f"[Step 4] Regenerated SRT generation failed: {e} Video path is : {video_path}")
                        return cls.call_webhook(
                            request=request,
                            status_code=400,
                            message=f"Unable to process the video. {4}"
                        )
            else:
                cls.LOGGER.info("Full video edit — basic SRT analysis.")
                response = GeminiService().analyze_srt_basic(srt_content=srt_content, color_list=highlight_colors)
                if isinstance(response, list):
                    highlighted_words = {cw.word: cw.color for cw in response}
                    cls.LOGGER.debug(f"Highlighted words: {highlighted_words}")

            output_videos = []

            for aspect_ratio in aspect_ratios:
                cls.LOGGER.info(f"Step 5: Processing aspect ratio {aspect_ratio}...")
                try:
                    ass_file = SubtitleService.generate_ass_file(
                        request=request,
                        folder=media_folder,
                        srt_file_path=srt_file,
                        aspect_ratio=aspect_ratio,
                        highlighted_words=highlighted_words
                    )
                    cls.LOGGER.info(f"Generated ASS file for {aspect_ratio}: {ass_file}")
                except Exception as e:
                    cls.LOGGER.error(f"[Step 5] ASS file generation failed for {aspect_ratio}: {e} Video path is : {video_path}")
                    return cls.call_webhook(
                        request=request,
                        status_code=400,
                        message=f"Unable to process the video. {5}"
                    )

                try:
                    cropped_video_path = VideoCropService.crop_video(
                        video_path=video_path,
                        folder=media_folder,
                        aspect_ratio=aspect_ratio
                    )
                    cls.LOGGER.info(f"Cropped video for {aspect_ratio}: {cropped_video_path}")
                except Exception as e:
                    cls.LOGGER.error(f"[Step 5] Cropping failed for {aspect_ratio}: {e} Video path is : {video_path}")
                    return cls.call_webhook(
                        request=request,
                        status_code=400,
                        message=f"Unable to process the video. {6}"
                    )

                try:
                    video_output = VideoCropService.burn_subtitle(
                        folder=media_folder,
                        croped_video_path=cropped_video_path,
                        ass_file_path=ass_file,
                        aspect_ratio=aspect_ratio
                    )
                    cls.LOGGER.info(f"Final output for {aspect_ratio}: {video_output}")
                    video_url = f"{VideoSettings.BASE_URL}{video_output}"
                    output_videos.append(WebhookVideo(video_url=video_url, aspect_ratio=aspect_ratio))
                except Exception as e:
                    cls.LOGGER.error(f"[Step 5] Burning subtitle failed for {aspect_ratio}: {e} Video path is : {video_path}")
                    return cls.call_webhook(
                        request=request,
                        status_code=400,
                        message=f"Unable to process the video. {7}"
                    )

            cls.LOGGER.info("Step 6: All output videos generated successfully.")
            for v in output_videos:
                cls.LOGGER.debug(f"Generated video: {v.aspect_ratio} -> {v.video_url}")

            cls.call_webhook(
                request=request,
                status_code=200,
                message="Video processing complete",
                data=output_videos
            )
            temp_folder = os.path.join(cls.MEDIA_ROOT, media_folder.removeprefix("media/"), 'temp')
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)
                cls.LOGGER.info(f"Removed temporary folder: {temp_folder}")
            else:
                cls.LOGGER.info(f"No temporary folder found to remove: {temp_folder}")

            # Remove the original video file if it exists
            # video_path = os.path.join(cls.MEDIA_ROOT, media_folder.removeprefix("media/"), VideoSettings.VIDEO_FILE)
            # if os.path.exists(video_path):
            #     os.remove(video_path)
            #     cls.LOGGER.info(f"Removed video file: {video_path}")
            # else:
            #     cls.LOGGER.info(f"No video file found to remove: {video_path}")

        except ValueError as e:
            cls.LOGGER.error(f"[ValueError] {e} Video path is : {video_path}")
            return cls.call_webhook(
                request=request,
                status_code=400,
                message=f"Unable to process the video. {8}"
            )
        except Exception as e:
            cls.LOGGER.error(f"[Unhandled Exception] {e} Video path is : {video_path}")
            return cls.call_webhook(
                request=request,
                status_code=400,
                message=f"Unable to process the video. {9}"
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
        
