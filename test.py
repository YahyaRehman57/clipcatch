import os
from datetime import timedelta
import whisper
import ffmpeg
import argparse

# Constants (you can change or expose as CLI args)
TEMP_AUDIO_FILE = "temp_audio.wav"
TEMP_SRT_FILE = "subtitles.srt"

def format_timestamp(seconds):
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    millis = int((td.total_seconds() - total_seconds) * 1000)
    return f"{str(td)}".split('.')[0].zfill(8).replace('.', ',') + f",{millis:03d}"

def split_segment(segment, max_words=6):
    words = segment["text"].strip().split()
    total_words = len(words)
    if total_words == 0:
        return []

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

def generate_srt_file(video_path: str, output_folder: str, max_words_per_subtitle: int = 6):
    os.makedirs(os.path.join(output_folder, 'temp'), exist_ok=True)
    audio_path = os.path.join(output_folder, 'temp', TEMP_AUDIO_FILE)
    srt_path = os.path.join(output_folder, 'temp', TEMP_SRT_FILE)

    # Extract audio
    (
        ffmpeg
        .input(video_path)
        .output(audio_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000')
        .overwrite_output()
        .run()
    )
    print(f"[*] Audio extracted to {audio_path}")

    # Load Whisper and transcribe
    audio = whisper.load_audio(audio_path)
    model = whisper.load_model("base", device="cpu")
    result = whisper.transcribe(model, audio, language="en")

    # Create SRT content
    srt_lines = []
    counter = 1
    for segment in result['segments']:
        smaller_segments = split_segment(segment, max_words=max_words_per_subtitle)
        for sub in smaller_segments:
            start = format_timestamp(sub["start"])
            end = format_timestamp(sub["end"])
            text = sub["text"]
            srt_lines.append(f"{counter}\n{start} --> {end}\n{text}\n")
            counter += 1

    # Save to file
    with open(srt_path, "w", encoding="utf-8") as f:
        f.writelines(srt_lines)

    print(f"[+] SRT file written to: {srt_path}")
    return srt_path if os.path.exists(srt_path) else None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate subtitles from a video file using Whisper.")
    parser.add_argument("--video", required=True, help="Path to the input video file")
    parser.add_argument("--output", required=True, help="Folder to save outputs")
    parser.add_argument("--max-words", type=int, default=6, help="Max words per subtitle line (default: 6)")

    args = parser.parse_args()
    generate_srt_file(args.video, args.output, args.max_words)
