import os
from typing import List, Dict

class VideoSettings:
    BASE_URL = os.getenv("API_URL", "")
    DEFAULT_ASPECT_RATIOS: List[str] = ["16:9", "4:3", "1:1", "9:16", "21:9"]

    # Default font and font sizes
    DEFAULT_FONT: str = "Luckiest Guy"

    # Define default font sizes for each aspect ratio
    DEFAULT_FONT_SIZES: Dict[str, int] = {
        "16:9": 22,
        "4:3": 20,
        "1:1": 18,
        "9:16": 20,
        "21:9": 22,
    }

    HIGHLIGHT_COLORS: List[str] = [
        "&H00FF00&",  # green
        "&H0000FF&",  # blue
        "&HFFFF00&",  # yellow
        "&HFF00FF&",  # magenta
        "&H00FFFF&",  # cyan
        "&HFFA500&",  # orange
        "&H800080&",  # purple
        "&H808080&",  # gray
        "&HFFD700&",  # gold
    ]

    COLOR_REGEX = r"^&H[0-9A-Fa-f]{6}&"

    AVAILABLE_FONTS: List[str] = [
        "Arial",
        "Luckiest Guy",
        "Helvetica",
        "Times New Roman",
        "Courier New",
        "Georgia",
    ]

    DEFAULT_LANGUAGE_CODE = "en"

    LANGUAGE_CODES = [
        "en",    # English
        "es",    # Spanish
        "fr",    # French
        "de",    # German
        "it",    # Italian
        "pt",    # Portuguese
        "ru",    # Russian
        "zh",    # Chinese
        "ja",    # Japanese
        "ko",    # Korean
        "hi"     # Hindi
    ]


    VIDEO_FILE = "video.mp4"
    TEMP_CLIPS_DIR = "temp/clips"
    OUTPUT_DIR = "output"
    TEMP_AUDIO_FILE_PATH = "temp/audio.wav"
    TEMP_SRT_FILE_PATH = "temp/output.srt"
    TEMP_ASS_FILE_PATH = "temp/output.ass"

    MAX_WORDS_PER_SUBTITLE = 4 

    WHISPER_MODEL = "base"

    STATIC_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "static")
    )

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

    @classmethod
    def generate_ass_header(cls, selected_font: str, font_size: int) -> str:
        return f"""[Script Info]
            Title: Highlighted Subtitles
            ScriptType: v4.00+
            Collisions: Normal
            PlayDepth: 0

            [V4+ Styles]
            Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
            Style: Default,{selected_font},{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,2,2,50,50,50,1

            [Events]
            Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
        """

