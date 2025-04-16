import logging
import traceback
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

from app.settings import settings

logger = logging.getLogger(__name__)


YOUTUBE_API = "https://youtube.googleapis.com"


class YoutubeChannelInfo(BaseModel):
    id: str
    title: str
    thumbnail: str


async def get_channel_subscriptions(channel_id: str):
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "key": settings.google_api_key,
    }
    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(
                urljoin(YOUTUBE_API, "/youtube/v3/subscriptions"), params=params
            )
            response.raise_for_status()
            json = response.json()
            channels: list[YoutubeChannelInfo] = []
            for item in json.get("items", []):
                snippet = item.get("snippet")
                resource_id = snippet.get("resourceId")
                channel_id = resource_id.get("channelId")
                channel_title = snippet.get("title")
                thumbnails = snippet.get("thumbnails")
                channel_thumbnail = thumbnails.get("high", {}).get("url")
                try:
                    channels.append(
                        YoutubeChannelInfo(
                            id=channel_id,
                            title=channel_title,
                            thumbnail=channel_thumbnail,
                        )
                    )
                except TypeError:
                    logger.exception(traceback.format_exc())
            yield channels
            params["pageToken"] = json.get("nextPageToken")
            if params.get("pageToken", None) is None:
                break


async def get_channel_info(channel_id: str):
    url = "https://www.youtube.com/"
    if channel_id.startswith("@"):
        url += channel_id
    else:
        url += f"channel/{channel_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url)
        if response.is_error:
            return None
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        channel_id_tag = soup.find("meta", itemprop="identifier")
        if not channel_id_tag:
            channel_id_tag = soup.find("meta", itemprop="channelId")
        name_tag = soup.find("meta", itemprop="name")
        thumbnail_tag = soup.find("link", itemprop="thumbnailUrl")
        try:
            return YoutubeChannelInfo(
                id=channel_id_tag["content"],
                title=name_tag["content"],
                thumbnail=thumbnail_tag["href"],
            )
        except TypeError:
            logger.exception(traceback.format_exc())
            return None


async def _get_channel_upload_playlist_id(channel_id: str):
    params = {
        "part": "contentDetails",
        "id": channel_id,
        "key": settings.google_api_key,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            urljoin(YOUTUBE_API, "/youtube/v3/channels"), params=params
        )
        response.raise_for_status()
        json = response.json()
        uploads_playlist_id = json["items"][0]["contentDetails"]["relatedPlaylists"][
            "uploads"
        ]
        return uploads_playlist_id


async def _get_channel_upload_playlist_videos(channel_id: str):
    channel_upload_playlist_id = await _get_channel_upload_playlist_id(channel_id)
    params = {
        "part": "contentDetails",
        "playlistId": channel_upload_playlist_id,
        "maxResults": 50,
        "key": settings.google_api_key,
    }
    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(
                urljoin(YOUTUBE_API, "/youtube/v3/playlistItems"), params=params
            )
            response.raise_for_status()
            json = response.json()
            video_ids = []
            for item in json.get("items", []):
                content_details = item.get("contentDetails")
                video_id = content_details.get("videoId")
                video_ids.append(video_id)
            yield video_ids
            params["pageToken"] = json.get("nextPageToken")
            if params.get("pageToken", None) is None:
                break


class YoutubeVideoInfo(BaseModel):
    id: str
    title: str
    thumbnail: str
    category_id: int
    description: str
    published: str


async def get_channel_latest_videos(channel_id: str):
    async for video_ids in _get_channel_upload_playlist_videos(channel_id):
        params = {
            "part": "snippet",
            "id": ",".join(video_ids),
            "key": settings.google_api_key,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                urljoin(YOUTUBE_API, "/youtube/v3/videos"), params=params
            )
            response.raise_for_status()
            json = response.json()
            videos: list[YoutubeVideoInfo] = []
            for item in json.get("items", []):
                snippet = item.get("snippet")
                video_id = item.get("id")
                title = snippet.get("title")
                category_id = int(snippet.get("categoryId"))
                description = snippet.get("description")
                published = snippet.get("publishedAt")
                thumbnails = snippet.get("thumbnails")
                video_thumbnail = thumbnails.get("high", {}).get("url")
                try:
                    videos.append(
                        YoutubeVideoInfo(
                            id=video_id,
                            title=title,
                            thumbnail=video_thumbnail,
                            category_id=category_id,
                            description=description,
                            published=published,
                        )
                    )
                except TypeError:
                    logger.exception(traceback.format_exc())
            yield videos


class YoutubeVideoCategory(BaseModel):
    id: int
    name: str


async def get_video_category(category_id: str):
    params = {
        "part": "snippet",
        "id": category_id,
        "key": settings.google_api_key,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            urljoin(YOUTUBE_API, "/youtube/v3/videoCategories"), params=params
        )
        response.raise_for_status()
        json = response.json()
        category = json["items"][0]["snippet"]["title"]
        try:
            return YoutubeVideoCategory(id=category_id, name=category)
        except TypeError:
            logger.exception(traceback.format_exc())
            return None


async def get_video_categories():
    params = {
        "part": "snippet",
        "regionCode": "US",
        "key": settings.google_api_key,
    }
    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(
                urljoin(YOUTUBE_API, "/youtube/v3/videoCategories"), params=params
            )
            response.raise_for_status()
            json = response.json()
            categories: list[YoutubeVideoCategory] = []
            for item in json.get("items", []):
                category_id = int(item.get("id"))
                category_name = item.get("snippet").get("title")
                try:
                    categories.append(
                        YoutubeVideoCategory(id=category_id, name=category_name)
                    )
                except TypeError:
                    logger.exception(traceback.format_exc())
            yield categories
            params["pageToken"] = json.get("nextPageToken")
            if params.get("pageToken", None) is None:
                break


async def get_video_uploader(video_id: str):
    url = "https://www.youtube.com/watch?v=" + video_id
    async with httpx.AsyncClient() as client:
        response = await client.get(url=url)
        if response.is_error:
            return None
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        if author_span := soup.find("span", itemprop="author"):
            if author_name_link := author_span.find("link", itemprop="name"):
                return author_name_link.attrs.get("content")
        return None
