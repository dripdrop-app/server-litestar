import asyncio
from pathlib import Path


async def convert_audio_to_mp3(audio_file: str):
    file = Path(audio_file)
    if file.suffix == ".mp3":
        return audio_file
    output_filename = f"{file.stem}.mp3"
    process = await asyncio.subprocess.create_subprocess_exec(
        "ffmpeg",
        "-i",
        audio_file,
        "-b:a",
        "320k",
        output_filename,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    error = await process.stderr.read()
    await process.wait()
    if process.returncode != 0:
        raise Exception(error.decode())
    return output_filename
