import re
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Union
from app.core.config import VideoSettings
from urllib.parse import urlparse


class VideoEditRequest(BaseModel):

    video_url: str
    webhook_url: str
    max_words_per_subtitle: int = VideoSettings.MAX_WORDS_PER_SUBTITLE
    aspect_ratios: Optional[List[str]] = ["16:9"]
    selected_font: Optional[str] = VideoSettings.DEFAULT_FONT
    font_sizes: Optional[Dict[str, int]] = {}
    # highlighted_words: Optional[Dict[str, Optional[str]]] = {}
    highlighted_words: Optional[Union[Dict[str, Optional[str]], List[str]]] = {}
    highlight_colors: Optional[List[str]] = []
    is_full_video_edit: Optional[bool] = True
    
    # It will be sent as it is in the webhook the goal is to identify the reuqest
    metadata: Optional[Dict[str, str]] = {}

    @field_validator('video_url')
    def validate_video_url(cls, v):
        parsed = urlparse(v)
        if not all([parsed.scheme in ("http", "https"), parsed.netloc]):
            raise ValueError("video_url must be a valid HTTP or HTTPS URL.")
        return v
    
    @field_validator('webhook_url')
    def validate_video_url(cls, v):
        parsed = urlparse(v)
        if not all([parsed.scheme in ("http", "https"), parsed.netloc]):
            raise ValueError("video_url must be a valid HTTP or HTTPS URL.")
        return v
    
    @field_validator('font_sizes')
    def validate_font_sizes_keys(cls, v):
        if v:
            valid_aspect_ratios = VideoSettings.get_aspect_ratios()
            for ratio in v.keys():
                if ratio not in valid_aspect_ratios:
                    raise ValueError(f"Invalid aspect ratio in font_size: '{ratio}'. Must be one of: {', '.join(valid_aspect_ratios)}")
        return v


    @field_validator('aspect_ratios')
    def validate_aspect_ratios(cls, v: List[str]) -> List[str]:
        default_aspect_ratios = VideoSettings.get_aspect_ratios()
        invalid = [ratio for ratio in v if ratio not in default_aspect_ratios]
        if invalid:
            raise ValueError(f"Invalid aspect ratios: {', '.join(invalid)}. Must be one of: {', '.join(default_aspect_ratios)}")
        return v

    @field_validator('selected_font')
    def validate_selected_font(cls, v):
        available_fonts = VideoSettings.get_available_fonts()
        if v not in available_fonts:
            raise ValueError(f"Font '{v}' is not available. Please provide the corresponding TTF file.")
        return v
    
    @field_validator('highlighted_words')
    def validate_highlighted_words(cls, v, values):
        if v:
            if isinstance(v, dict):
                for word, color in v.items():
                    if color is not None and (not isinstance(color, str) or not re.match(VideoSettings.COLOR_REGEX, color)):
                        raise ValueError(f"Invalid color format: {color}. It must be in the format &HXXXXXX&")
            elif isinstance(v, list):
                for word in v:
                    if not isinstance(word, str):
                        raise ValueError("All items in the list must be strings.")
                    if re.match(VideoSettings.COLOR_REGEX, word):
                        raise ValueError(f"Invalid word: {word}. Words must not be color codes.")
            else:
                raise TypeError("highlighted_words must be either a dict or a list.")
        return v

    @field_validator('highlight_colors')
    def validate_highlight_colors(cls, v):
        if v:
            for color in v:
                if not isinstance(color, str) or not re.match(VideoSettings.COLOR_REGEX, color):
                    raise ValueError(f"Invalid color format: {color}. It must be in the format &HXXXXXX&")
        return v

    @field_validator('is_full_video_edit')
    def validate_is_full_video_edit(cls, v):
        if not isinstance(v, bool):
            raise ValueError("is_full_video_edit must be a boolean: True (edit full video) or False (extract viral clips).")
        return v
    class Config:
        json_schema_extra = {
            "example": {
                "video_url": "https://example.com/sample-video.mp4",
                "webhook_url": "https://example.com/webhook",
                "aspect_ratios": ["9:16"],
                "selected_font": "Arial",
                "font_size": {
                    "9:16": 20
                },
                "highlighted_words": {
                    "important": "&H00FF00&",
                    "listen": None  # will use default or rotate from highlight_colors
                },
                "highlight_colors": [
                    "&HFF0000&",
                    "&H00FF00&",
                    "&H0000FF&"
                ],
                "is_full_video_edit": True
            }
        }


class WebhookVideo(BaseModel):
    video_url: str
    aspect_ratio: str


class WebhookVideoResponse(BaseModel):
    message: str
    status_code: int
    metadata: Optional[Dict[str, str]] = {}
    videos: Optional[List[WebhookVideo]] = None


class VideoEditResponse(BaseModel):
    status: str
    output_video_path: str
