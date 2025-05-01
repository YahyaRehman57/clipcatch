import time, os, json, re
import google.generativeai as genai
from typing import List, Union
from pydantic import ValidationError
from app.schemas.ai_model import ColoredWord, AdvancedSRTResponse
from app.config.logger import LogManager

class GeminiService:
    LOGGER = LogManager.get_logger("gemini_service")

    BASIC_PROMPT_TEMPLATE = """
    You are given two inputs:
    1. The content of a subtitle file (in .srt format).
    2. A list of colors.

    Your task is to:
    - Identify a selection of the most emotionally meaningful, thematically important, or visually evocative words from the subtitle text.
    - Assign a color to each selected word using the provided color list. The color must match the emotional tone or "vibe" of the word.

    Word Selection Guidelines:
    - Only include words that actually appear in the subtitle text.
    - Each word should be listed only once.
    - Focus on emotionally resonant, human-centered, or visually striking words:
    - Strong nouns (e.g., "mother", "storm", "home", "death", "freedom", "tears")
    - Dynamic verbs (e.g., "run", "scream", "break", "hold", "fight", "whisper")
    - Emotional adjectives (e.g., "furious", "lonely", "brave", "beautiful", "afraid", "cold")
    - Avoid:
    - Common or neutral words (e.g., "said", "get", "go", "thing", "okay", "good")
    - Filler or function words (e.g., "the", "is", "it", "you", "and", "of")

    Color Assignment Guidelines:
    - Use colors that reflect the emotional tone of the word:
    - 🔥 Warm colors (reds, oranges, yellows): passion, anger, danger, excitement
    - 🌊 Cool colors (blues, greens): sadness, calm, reflection, isolation
    - 🎨 Purples and pinks: creativity, emotion, gentleness, vulnerability
    - DO NOT use low-contrast or "funky" colors. Explicitly avoid:
    - Deep/dark blues (e.g., #00008B)
    - Neon colors (e.g., #00FFFF, #FF00FF)
    - Pale pastels or grays (e.g., #CCCCCC, #FFFFE0)
    - All selected colors must be high contrast and fully legible on a black background.

    Use the examples above as a guide when selecting words and colors. Think emotionally, not just literally.

    Respond with a list of objects like:
    [
    {{ "word": "example", "color": "#FF0000" }},
    ...
    ]
    Only include words that appear in the subtitle text.


    Subtitle content:
    {srt_content}


    Color list:
    {colors}

    """

    ADVANCED_PROMPT_TEMPLATE = """
    You are given two inputs:
    1. The content of a subtitle file (in .srt format).
    2. A list of colors.

    Your tasks are:

    1. Identify the most emotionally resonant and thematically important words from the subtitle text:
    - Only include words that actually appear in the subtitle.
    - Each word should be unique (no duplicates).
    - Focus on:
        - Strong nouns (e.g., "mother", "storm", "home", "death", "freedom", "tears")
        - Dynamic verbs (e.g., "run", "scream", "break", "hold", "fight", "whisper")
        - Emotional adjectives (e.g., "furious", "lonely", "brave", "beautiful", "afraid", "cold")
    - Avoid generic or filler words:
        - Examples to avoid: "thing", "get", "go", "okay", "the", "is", "it", "you"

    2. Assign each word a color from the provided list based on its emotional tone:
    - 🔥 Warm colors (reds, oranges, yellows) → passion, anger, excitement
    - 🌊 Cool colors (blues, greens) → sadness, calm, reflection
    - 🎨 Purples and pinks → creativity, emotion, gentleness
    - Avoid using:
        - Deep blues (e.g., #00008B)
        - Neon tones (e.g., #00FFFF, #FF00FF)
        - Pale pastels or low-contrast colors (e.g., #CCCCCC, #FFFFE0)
    - All colors must be highly legible on a black background.

    3. Determine the **active speech range** from the subtitle:
    - Identify the timestamp of the first subtitle that contains real spoken dialogue (skip silent intros or music cues).
    - Identify the timestamp of the last subtitle that includes meaningful dialogue (ignore end credits, silence, or outro music).

    Use the examples above as guidance. Think emotionally and visually.

    Return the result in the following JSON format:
    {{
    "colored_words": [
        {{ "word": "example", "color": "#FF0000" }},
        ...
    ],
    "active_speech_range": {{
        "start_time": "00:00:12,000",
        "end_time": "00:02:45,500"
    }}
    }}


    Subtitle content:
    {srt_content}


    Color list:
    {colors}
    """

    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel('models/gemini-1.5-flash')
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _generate_with_retry(self, prompt: str) -> str:
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                if attempt == self.max_retries:
                    return f"Error after {self.max_retries} retries: {str(e)}"
                else:
                    self.LOGGER.debug(f"Attempt {attempt} failed: {e}. Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)

    def _generate_with_retry(self, prompt: str) -> str:
        self.LOGGER.info("Generating content with retry logic")
        for attempt in range(1, self.max_retries + 1):
            try:
                self.LOGGER.debug("Attempt %d: Sending prompt to Gemini model", attempt)
                response = self.model.generate_content(prompt)
                self.LOGGER.info("Response received successfully on attempt %d", attempt)
                return response.text.strip()
            except Exception as e:
                self.LOGGER.warning("Attempt %d failed: %s", attempt, str(e))
                if attempt == self.max_retries:
                    self.LOGGER.error("Max retries reached. Returning error response.")
                    return f"Error after {self.max_retries} retries: {str(e)}"
                self.LOGGER.info("Retrying in %d seconds...", self.retry_delay)
                time.sleep(self.retry_delay)

    def analyze_srt_basic(self, srt_content: str, color_list: List[str]) -> List[ColoredWord]:
        self.LOGGER.info("Starting basic SRT analysis")

        # Use JSON string representation for consistent formatting in prompt
        colors_json = json.dumps(color_list, ensure_ascii=False)
        prompt = self.BASIC_PROMPT_TEMPLATE.format(srt_content=srt_content, colors=colors_json)

        self.LOGGER.debug("Constructed prompt for basic analysis")
        response = self._generate_with_retry(prompt)

        self.LOGGER.debug("Raw response: %s", response)

        # Remove surrounding code block markers if present
        cleaned = re.sub(r"^```(?:json)?|```$", "", response.strip(), flags=re.MULTILINE).strip()

        self.LOGGER.debug("Cleaned response: %s", cleaned)

        try:
            parsed = json.loads(cleaned)
            colored_words = [ColoredWord(**item) for item in parsed]
            self.LOGGER.info("Parsed %d colored words successfully", len(colored_words))
            return colored_words
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            self.LOGGER.error("Error parsing basic response: %s", str(e))
            self.LOGGER.error("Cleaned response was: %s", cleaned)
            return []

    def analyze_srt_advanced(self, srt_content: str, color_list: List[str]) -> Union[AdvancedSRTResponse, dict]:
        self.LOGGER.info("Starting advanced SRT analysis")
        self.LOGGER.info("Colors list: %s", color_list)

        # Serialize color list to JSON for accurate inclusion in prompt
        colors_json = json.dumps(color_list, ensure_ascii=False)
        self.LOGGER.debug("Serialized colors for prompt: %s", colors_json)

        prompt = self.ADVANCED_PROMPT_TEMPLATE.format(srt_content=srt_content, colors=colors_json)
        self.LOGGER.debug("Constructed prompt for advanced analysis:\n%s", prompt)

        response = self._generate_with_retry(prompt)
        self.LOGGER.debug("Raw response: %s", response)

        # Remove optional triple backtick formatting (e.g., ```json ... ```)
        cleaned = re.sub(r"^```(?:json)?|```$", "", response.strip(), flags=re.MULTILINE).strip()
        self.LOGGER.debug("Cleaned response: %s", cleaned)

        try:
            parsed = json.loads(cleaned)
            result = AdvancedSRTResponse(**parsed)
            self.LOGGER.info("Parsed advanced response successfully: %s", result)
            return result
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            self.LOGGER.error("Failed to parse advanced response: %s", str(e))
            self.LOGGER.debug("Traceback:", exc_info=True)
            self.LOGGER.error("Cleaned response content: %s", cleaned)
            return {"raw_response": response}