import subprocess

async def run_ffmpeg_commands(input_path, output_path):
    # Example ffmpeg command: cut first 10 seconds
    command = [
        "ffmpeg", "-i", input_path, "-ss", "00:00:00", "-t", "00:00:10", "-c", "copy", output_path
    ]
    subprocess.run(command, check=True)
