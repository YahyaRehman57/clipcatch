import os, ffmpeg, re
import whisper_timestamped as whisper


from app.schemas.video_schema import VideoEditRequest
from app.core.config import VideoSettings
from datetime import timedelta
from typing import Dict

class SubtitleService:
    
    @classmethod
    def generate_srt_file(cls, request: VideoEditRequest, folder: str, video_path: str):
        def format_timestamp(seconds):
            td = timedelta(seconds=seconds)
            total_seconds = int(td.total_seconds())
            millis = int((td.total_seconds() - total_seconds) * 1000)
            return f"{str(td)}".split('.')[0].zfill(8).replace('.', ',') + f",{millis:03d}"
        
        def split_segment(segment, max_words=6):
            words = segment["text"].strip().split()
            total_words = len(words)
            duration = segment["end"] - segment["start"]
            word_duration = duration / total_words

            sub_segments = []
            for i in range(0, total_words, max_words):
                chunk_words = words[i:i+max_words]
                chunk_start = segment["start"] + i * word_duration
                chunk_end = chunk_start + len(chunk_words) * word_duration
                sub_segments.append({
                    "start": chunk_start,
                    "end": chunk_end,
                    "text": " ".join(chunk_words)
                })
            return sub_segments



        os.makedirs(os.path.join(folder, 'temp'), exist_ok=True)
        output_audio_path = os.path.join(folder, VideoSettings.TEMP_AUDIO_FILE_PATH)
        output_srt_path = os.path.join(folder, VideoSettings.TEMP_SRT_FILE_PATH)
        max_words_per_subtitle = request.max_words_per_subtitle

        (
            ffmpeg
            .input(video_path)
            .output(output_audio_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000')
            .overwrite_output()
            .run()
        )

        audio = whisper.load_audio(output_audio_path)
        model = whisper.load_model(VideoSettings.WHISPER_MODEL, device="cpu")
        result = whisper.transcribe(model, audio, language="en")

        srt_lines = []
        counter = 1
        for i, segment in enumerate(result['segments']):
            # start = format_timestamp(segment['start'])
            # end = format_timestamp(segment['end'])
            # text = segment['text'].strip()
            # srt_lines.append(f"{i+1}\n{start} --> {end}\n{text}\n")

            smaller_segments = split_segment(segment, max_words=max_words_per_subtitle)
            for sub in smaller_segments:
                start = format_timestamp(sub["start"])
                end = format_timestamp(sub["end"])
                text = sub["text"]
                srt_lines.append(f"{counter}\n{start} --> {end}\n{text}\n")
                counter += 1


        # Save to file
        with open(output_srt_path, "w", encoding="utf-8") as srt_file:
            srt_file.writelines(srt_lines)

        return output_srt_path if os.path.exists(output_srt_path) else None

    @classmethod
    def srt_to_ass_timestamp(cls, srt_time):
        hms, ms = srt_time.split(',')
        hours, minutes, seconds = map(int, hms.split(':'))
        centiseconds = int(int(ms) / 10)
        return f"{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}"


    @classmethod
    def parse_srt_file(cls, srt_file_path: str):
        with open(srt_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        pattern = re.compile(r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)\s*(?=\n\d+\s+\d{2}:\d{2}:\d{2},\d{3}|$)', re.DOTALL)
        matches = pattern.findall(content)

        subtitles = []
        for _, start, end, text in matches:
            # Replace line breaks within subtitle text with space
            cleaned_text = ' '.join(text.strip().splitlines())
            subtitles.append({'start': start.strip(), 'end': end.strip(), 'text': cleaned_text})
        return subtitles

    @staticmethod
    def srt_to_ass_timestamp(ts: str) -> str:
        h, m, s_ms = ts.split(':')
        s, ms = s_ms.split(',')
        return f"{int(h):01}:{int(m):02}:{int(s):02}.{int(ms)//10:02}"

    @staticmethod
    def rgb_to_ass_bgr(color: str) -> str:
        """Convert #RRGGBB to BGR hex for ASS color format"""
        color = color.lstrip('#')
        r, g, b = color[0:2], color[2:4], color[4:6]
        return f"{b}{g}{r}"

    @classmethod
    def generate_ass_file(cls, request: VideoEditRequest, srt_file_path: str, folder: str, aspect_ratio: str, highlighted_words: dict):
        
        subtitles = cls.parse_srt_file(srt_file_path)
        font_sizes = request.font_sizes
        font_size = font_sizes.get(aspect_ratio) or VideoSettings.DEFAULT_FONT_SIZES.get(aspect_ratio) or 24
        selected_font = request.selected_font
        ass_file_path = os.path.join(folder, VideoSettings.TEMP_ASS_FILE_PATH)

        with open(ass_file_path, 'w', encoding='utf-8') as f:
            ass_header = VideoSettings.generate_ass_header(selected_font, font_size)
            f.write(ass_header)

            for sub in subtitles:
                start = cls.srt_to_ass_timestamp(sub['start'])
                end = cls.srt_to_ass_timestamp(sub['end'])
                text = sub['text']
                words = text.split()
                final_text = ""

                for word in words:
                    clean_word = re.sub(r'\W+', '', word).lower()
                    if clean_word in highlighted_words:
                        color_hex = cls.rgb_to_ass_bgr(highlighted_words[clean_word])
                        final_text += f"{{\\1c&H{color_hex}&}}{word}{{\\r}} "
                    else:
                        final_text += word + " "

                final_text = final_text.strip()
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{final_text}\n")

        return ass_file_path