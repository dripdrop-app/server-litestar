import asyncio

import yt_dlp


async def download_audio_from_video(download_path: str, url: str):
    def _download_audio_from_video():
        ydl_opts = {
            "format": "best",
            "fixup": "never",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "0",
                }
            ],
            "outtmpl": download_path,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)

    return await asyncio.to_thread(_download_audio_from_video)


async def extract_video_info(url: str):
    def _extract_video_info():
        with yt_dlp.YoutubeDL() as ydl:
            return ydl.extract_info(url, download=False)

    return await asyncio.to_thread(_extract_video_info)
