import shutil
import os
from app.utils.ffmpeg_utils import run_ffmpeg_commands

async def process_video(file):
    input_path = f"temp_inputs/{file.filename}"
    output_path = f"temp_outputs/edited_{file.filename}"

    os.makedirs("temp_inputs", exist_ok=True)
    os.makedirs("temp_outputs", exist_ok=True)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 👇 This is your AI + ffmpeg processing function
    await run_ffmpeg_commands(input_path, output_path)

    return output_path
