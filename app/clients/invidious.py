from urllib.parse import urljoin

import aiofiles
import httpx
from pydantic import BaseModel, Field

from app.settings import settings


class ChannelVideosResponse(BaseModel):
    videos: list[dict]
    continuation: str | None = Field(None)


async def get_youtube_video_info(video_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            urljoin(settings.invidious_api_url, f"/api/v1/videos/{video_id}")
        )
        if response.is_error:
            raise Exception("Failed to retrieve video info")
        return response.json()


async def download_audio_from_youtube_video(video_id: str, download_path: str):
    video_info = await get_youtube_video_info(video_id)
    adaptive_formats = video_info.get("adaptiveFormats", [])
    audio_formats = [
        adaptive_format
        for adaptive_format in adaptive_formats
        if "audio" in adaptive_format["type"]
    ]
    if not audio_formats:
        raise Exception("No audio formats found")
    best_format = sorted(audio_formats, key=lambda x: x["bitrate"], reverse=True)[0]
    audio_url = best_format["url"]
    with aiofiles.open(download_path, mode="wb") as f:
        async with httpx.AsyncClient() as client:
            response = await client.get(audio_url)
            f.write(response.content)


async def get_youtube_channel_videos(channel_id: str, continuation_token: str = None):
    params = {}
    if continuation_token:
        params["continuation"] = continuation_token
    async with httpx.AsyncClient() as client:
        response = await client.get(
            urljoin(
                settings.invidious_api_url, f"/api/v1/channels/{channel_id}/videos"
            ),
            params=params,
        )
        if response.is_error:
            raise Exception("Failed to retrieve videos")
        json = response.json()
        new_continuation_token = json.get("continuation")
        videos = json.get("videos")
        return ChannelVideosResponse(videos=videos, continuation=new_continuation_token)
