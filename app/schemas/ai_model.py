from pydantic import BaseModel
from typing import List


class ColoredWord(BaseModel):
    word: str
    color: str


class ActiveSpeechRange(BaseModel):
    start_time: str
    end_time: str


class AdvancedSRTResponse(BaseModel):
    colored_words: List[ColoredWord]
    active_speech_range: ActiveSpeechRange
