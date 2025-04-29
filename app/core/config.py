from typing import List, Dict


class VideoSettings:
    DEFAULT_ASPECT_RATIOS: List[str] = ["16:9", "4:3", "1:1", "9:16", "21:9"]

    # Default font and font sizes
    DEFAULT_FONT: str = "Luckiest Guy"

    # Define default font sizes for each aspect ratio
    DEFAULT_FONT_SIZES: Dict[str, int] = {
        "16:9": 16,  # Default font size for 16:9 aspect ratio
        "4:3": 14,  # Default font size for 4:3 aspect ratio
        "1:1": 18,  # Default font size for 1:1 aspect ratio
        "9:16": 20,  # Default font size for 9:16 aspect ratio (vertical)
        "21:9": 22,  # Default font size for 21:9 aspect ratio
    }

    HIGHLIGHT_COLORS: List[str] = [
        "&HFF0000&",  # red
        "&H00FF00&",  # green
        "&H0000FF&",  # blue
        "&HFFFF00&",  # yellow
        "&HFF00FF&",  # magenta
        "&H00FFFF&",  # cyan
        "&HFFA500&",  # orange
        "&H800080&",  # purple
        "&HFFFFFF&",  # white
        "&H000000&",  # black
        "&H808080&",  # gray
        "&HFFD700&",  # gold
    ]

    COLOR_REGEX = r"^&H[0-9A-Fa-f]{6}&"

    AVAILABLE_FONTS: List[str] = [
        "Arial",
        "Helvetica",
        "Times New Roman",
        "Courier New",
        "Georgia",
    ]

    # AI Prompts (to generate video content or effects)
    AI_PROMPTS: dict = {
        "thumbnail_generation": "Generate a thumbnail with the title and the best frame.",
        "video_editing": "Edit the video by enhancing colors and trimming unnecessary scenes.",
        "highlight_scene": "Highlight the key scenes with text overlays.",
    }

    VIDEO_FILE = "video.mp4"
    TEMP_CLIPS_DIR = "temp/clips"
    OUTPUT_DIR = "output"
    TEMP_AUDIO_FILE_PATH = "temp/audio.wav"
    TEMP_SRT_FILE_PATH = "temp/output.srt"
    TEMP_ASS_FILE_PATH = "temp/output.ass"

    MAX_WORDS_PER_SUBTITLE = 4 

    WHISPER_MODEL = "base"

    @classmethod
    def get_aspect_ratios(cls):
        """Returns the list of available aspect ratios."""
        return cls.DEFAULT_ASPECT_RATIOS

    @classmethod
    def get_default_font(cls):
        """Returns the default font."""
        return cls.DEFAULT_FONT

    @classmethod
    def get_default_font_size(cls, aspect_ratio: str = "16:9") -> int:
        """Returns the default font size based on the aspect ratio."""
        return cls.DEFAULT_FONT_SIZES.get(
            aspect_ratio, 16
        )  # Default to 16 if aspect ratio not found

    @classmethod
    def get_highlighted_colors(cls):
        """Returns the default highlighted color."""
        return cls.HIGHLIGHT_COLORS

    @classmethod
    def get_available_fonts(cls):
        """Returns the list of available fonts."""
        return cls.AVAILABLE_FONTS

    @classmethod
    def get_ai_prompt(cls, key: str):
        """Fetches an AI prompt by its key."""
        return cls.AI_PROMPTS.get(key, "Prompt not found.")

    @classmethod
    def add_ai_prompt(cls, key: str, prompt: str):
        """Adds a new AI prompt to the list."""
        cls.AI_PROMPTS[key] = prompt

    @classmethod
    def remove_ai_prompt(cls, key: str):
        """Removes an AI prompt from the list."""
        if key in cls.AI_PROMPTS:
            del cls.AI_PROMPTS[key]
