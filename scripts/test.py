import re, os, ffmpeg, cv2
from faster_whisper import WhisperModel


# -------------------------
# Helper: Detect main object (face) in frame
def detect_main_object(frame):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)


    if len(faces) > 0:
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        center_x, center_y = x + w // 2, y + h // 2
        return center_x, center_y
    else:
        h, w = frame.shape[:2]
        return w // 2, h // 2


# -------------------------
# Helper: Crop video + keep audio
def crop_video(input_path, output_path, target_aspect_ratio=(9, 16)):
    probe = ffmpeg.probe(input_path)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    width, height = int(video_info['width']), int(video_info['height'])


    cap = cv2.VideoCapture(input_path)
    ret, frame = cap.read()
    cap.release()


    if not ret:
        raise Exception('Could not read video')


    center_x, center_y = detect_main_object(frame)


    target_w = width
    target_h = int(width * target_aspect_ratio[1] / target_aspect_ratio[0])


    if target_h > height:
        target_h = height
        target_w = int(height * target_aspect_ratio[0] / target_aspect_ratio[1])


    x1 = max(center_x - target_w // 2, 0)
    y1 = max(center_y - target_h // 2, 0)
    x1 = min(x1, width - target_w)
    y1 = min(y1, height - target_h)


    # Corrected ffmpeg call
    video = ffmpeg.input(input_path)
    cropped_video = video.video.filter('crop', target_w, target_h, x1, y1)
    audio = video.audio


    (
        ffmpeg
        .output(cropped_video, audio, output_path, vcodec='libx264', acodec='aac')
        .overwrite_output()
        .run()
    )




# -------------------------
# Helper: Transcribe original video audio
def transcribe_video_to_srt(input_video_path, output_srt_path, model_size="base"):
    MAX_WORDS_PER_SUBTITLE = 3


    print("[*] Loading Whisper model...")
    model = WhisperModel(model_size)


    os.makedirs('temp', exist_ok=True)
    output_audio_path = "temp/temp_audio.wav"


    print("[*] Extracting audio from original video...")
    (
        ffmpeg
        .input(input_video_path)
        .output(output_audio_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000')
        .overwrite_output()
        .run()
    )
    print(f"[*] Audio extracted to {output_audio_path}")


    print("[*] Starting transcription...")
    segments, info = model.transcribe(output_audio_path, beam_size=5)
    print("[*] Transcription finished.")


    def format_timestamp(seconds):
        hrs, secs = divmod(int(seconds), 3600)
        mins, secs = divmod(secs, 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"


    print(f"[*] Writing transcription to {output_srt_path}...")
    with open(output_srt_path, "w", encoding="utf-8") as f:
        subtitle_index = 1
        for segment in segments:
            words = segment.text.strip().split()
            num_words = len(words)
            duration = segment.end - segment.start
            avg_word_duration = duration / max(num_words, 1)


            for i in range(0, num_words, MAX_WORDS_PER_SUBTITLE):
                chunk_words = words[i:i + MAX_WORDS_PER_SUBTITLE]
                chunk_start_time = segment.start + (i * avg_word_duration)
                chunk_end_time = chunk_start_time + (len(chunk_words) * avg_word_duration)


                f.write(f"{subtitle_index}\n")
                f.write(f"{format_timestamp(chunk_start_time)} --> {format_timestamp(chunk_end_time)}\n")
                f.write(f"{' '.join(chunk_words)}\n\n")
                subtitle_index += 1


    print(f"✅ SRT file saved as {output_srt_path}")


# -------------------------
# Helper: Parse SRT
def parse_srt(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()


    entries = re.split(r'\n\s*\n', content.strip())
    subtitles = []


    for entry in entries:
        lines = entry.strip().split('\n')
        if len(lines) >= 3:
            times = lines[1]
            text = " ".join(lines[2:])
            start, end = times.split(' --> ')
            subtitles.append({
                'start': start.strip(),
                'end': end.strip(),
                'text': text.strip()
            })
    return subtitles


# -------------------------
# Helper: Convert timestamp for ASS format
def srt_to_ass_timestamp(srt_time):
    hms, ms = srt_time.split(',')
    hours, minutes, seconds = map(int, hms.split(':'))
    centiseconds = int(int(ms) / 10)
    return f"{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}"


# -------------------------
# Helper: Create ASS subtitles file
def create_ass(subtitles, output_path, highlight_words, highlight_color, font_name="Luckiest Guy", font_size=24):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"""[Script Info]
Title: Highlighted Subtitles
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0


[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,2,2,2,50,50,50,1


[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")


        for sub in subtitles:
            start = srt_to_ass_timestamp(sub['start'])
            end = srt_to_ass_timestamp(sub['end'])
            text = sub['text']


            words = text.split()
            final_text = ""
            # for word in words:
            #     clean_word = re.sub(r'\W+', '', word).lower()
            #     if clean_word in highlight_words:
            #         final_text += f"{{\\c{highlight_color}}}{word}{{\\c}} "
            #     else:
            #         final_text += word + " "
            for word in words:
                clean_word = re.sub(r'\W+', '', word).lower()
                if clean_word in highlight_words:
                    color = highlight_words[clean_word]
                    final_text += f"{{\\c{color}}}{word}{{\\c}} "
                else:
                    final_text += word + " "


            final_text = final_text.strip()


            f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{final_text}\n")


# -------------------------
# Helper: Burn ASS subtitles into video
def burn_subtitles(video_input, ass_file, video_output, fonts_dir=None):
    if os.path.exists(video_output):
        os.remove(video_output)


    ass_filter = f"ass={ass_file}"
    if fonts_dir:
        ass_filter += f":fontsdir={fonts_dir}"


    (
        ffmpeg
        .input(video_input)
        .output(
            video_output,
            vf=ass_filter,
            vcodec='libx264',
            acodec='copy',
            loglevel="error"
        )
        .overwrite_output()
        .run()
    )


# -------------------------
# Full crop and subtitle generation
def crop_for_all_aspects(original_video):
    output_dir = 'temp/clips'
    output_final_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(output_final_dir, exist_ok=True)


    aspect_ratios = {
        "9_16": (9, 16),
        "4_5": (4, 5),
        "1_1": (1, 1),
        "16_9": (16, 9),
    }


    # Transcribe ONCE from original
    srt_file = 'temp/output.srt'
    transcribe_video_to_srt(original_video, srt_file)
    subs = parse_srt(srt_file)


    highlight_words = {
        'important': '&H00FF00&',    # green
        'listen': '&H00FF00&',       # green
        'hearing': '&H00FF00&',      # green
        'moving': '&H00FF00&',       # green
        'questions': '&H00FF00&',    # green
        'validate': '&H00FF00&',     # green
        'challenge': '&H00FF00&',    # green
        'accountable': '&HFFFF00&',  # yellow
        'saying': '&HFFFF00&',       # yellow
        'avoiding': '&HFFFF00&',     # yellow
        'understand': '&HFFFF00&',   # yellow
        'resistance': '&HFFFF00&',   # yellow
        'normal': '&HFFFF00&'        # yellow
    }



    highlight_color = "&H00FF00&"  # green


    for name, ratio in aspect_ratios.items():
        cropped_video_path = os.path.join(output_dir, f"{name}.mp4")
        final_video_path = os.path.join(output_final_dir, f"{name}.mp4")


        # Different font size depending on aspect
        if name == "16_9":
            font_size = 24  # landscape: keep normal
        else:
            font_size = 18  # portrait/square: smaller


        ass_file = f'temp/converted_{name}.ass'
        create_ass(subs, ass_file, highlight_words, highlight_color, font_size=font_size)


        crop_video(original_video, cropped_video_path, target_aspect_ratio=ratio)
        burn_subtitles(cropped_video_path, ass_file, final_video_path, fonts_dir='fonts')


        print(f"✅ Final saved: {final_video_path}")


# -------------------------
# Main entry
def main():
    video_input = 'josh.mp4'
    crop_for_all_aspects(video_input)


if __name__ == "__main__":
    main()

