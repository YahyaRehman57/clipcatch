import requests, os, ffmpeg, cv2, tempfile
from typing import List
from app.schemas.video_schema import VideoEditRequest
from app.core.config import VideoSettings
from .gemini_service import GeminiService

class VideoCropService:

    @classmethod
    def detect_main_object(cls, frame):
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


    @classmethod
    def crop_video(cls, folder: str, video_path: str, aspect_ratio: str) -> List[str]:
        croped_path = os.path.join(folder, VideoSettings.TEMP_CLIPS_DIR)
        probe = ffmpeg.probe(video_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        width, height = int(video_info['width']), int(video_info['height'])


        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()


        if not ret:
            raise Exception('Could not read video')

        center_x, center_y = cls.detect_main_object(frame)
        target_w = width
        print("Aspect ratio is : ", aspect_ratio)
        w, h = map(int, aspect_ratio.split(":"))
        target_h = int(width * h / w)


        if target_h > height:
            target_h = height
            target_w = int(height * w / h)


        x1 = max(center_x - target_w // 2, 0)
        y1 = max(center_y - target_h // 2, 0)
        x1 = min(x1, width - target_w)
        y1 = min(y1, height - target_h)


        # Corrected ffmpeg call
        video = ffmpeg.input(video_path)
        cropped_video = video.video.filter('crop', target_w, target_h, x1, y1)
        audio = video.audio

        os.makedirs(croped_path, exist_ok=True)
        croped_file_path = os.path.join(croped_path, f'video_{aspect_ratio}.mp4'.replace(':', '_'))
        (
            ffmpeg
            .output(cropped_video, audio, croped_file_path, vcodec='libx264', acodec='aac')
            .overwrite_output()
            .run()
        )

        return croped_file_path

    @classmethod
    def srt_time_to_seconds(cls, time_str: str) -> float:
        """Convert 'HH:MM:SS,mmm' to seconds as float."""
        hh, mm, rest = time_str.split(":")
        ss, ms = rest.split(",")
        return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000


    @classmethod
    def trim_video(cls, video_file_path: str, start_time_str: float, end_time_str: float = None):
        if not os.path.exists(video_file_path):
            raise FileNotFoundError(f"Video file not found: {video_file_path}")
        
        start_time = cls.srt_time_to_seconds(start_time_str)
        input_kwargs = {'ss': start_time}
        output_kwargs = {'c': 'copy'}

        if end_time_str is not None:
            end_time = cls.srt_time_to_seconds(end_time_str)
            duration = end_time - start_time
            if duration <= 0:
                raise ValueError("End time must be greater than start time")
            output_kwargs['t'] = duration

        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(video_file_path)[1], delete=False) as tmpfile:
            temp_path = tmpfile.name

        try:
            (
                ffmpeg
                .input(video_file_path, **input_kwargs)
                .output(temp_path, **output_kwargs)
                .run(overwrite_output=True, quiet=True)
            )
            os.replace(temp_path, video_file_path)
            print(f"Video trimmed successfully: {video_file_path}")
        except ffmpeg.Error as e:
            os.remove(temp_path)
            raise RuntimeError(f"Failed to trim video: {e.stderr.decode()}") from e

    
    @classmethod
    def burn_subtitle(cls, folder: str, ass_file_path: str, croped_video_path, aspect_ratio: str):
        ass_path_fixed = ass_file_path.replace("\\", "/")
        ass_filter = f"ass='{ass_path_fixed}'"

        fonts_dir = os.path.join(VideoSettings.STATIC_DIR, "fonts").replace("\\", "/")
        print("Ass filter is : ", ass_filter)
        print("fonts dir is : ", fonts_dir)
        if fonts_dir:
            ass_filter += f":fontsdir={fonts_dir}"

        os.makedirs(os.path.join(folder, VideoSettings.OUTPUT_DIR), exist_ok=True)
        output_video_path = os.path.join(folder, VideoSettings.OUTPUT_DIR, f'video_{aspect_ratio}.mp4'.replace(':', '_'))
        ass_path_str = str(ass_file_path).replace("\\", "/")
        fonts_dir_str = str(fonts_dir).replace("\\", "/")

        vf_filter = f"ass='{ass_path_str}':fontsdir='{fonts_dir_str}'"
        (
            ffmpeg
            .input(croped_video_path)
            .output(
                output_video_path,
                vf=vf_filter,
                vcodec='libx264',
                acodec='copy',
                loglevel="error"
            )
            .overwrite_output()
            .run()
        )
        return output_video_path

