import asyncio
import base64
import io
import logging
import re
import shutil
import traceback
import uuid
from pathlib import Path

import aiofiles
import mutagen.id3

from app.models.music import TagsResponse
from app.services import tempfiles

logger = logging.getLogger(__name__)


class AudioTags:
    _TITLE_TAG = "TIT2"
    _ARTIST_TAG = "TPE1"
    _ALBUM_TAG = "TALB"
    _GROUPING_TAG = "TIT1"
    _ARTWORK_TAG = "APIC:"

    def __init__(self, file_path: str):
        self.tags = mutagen.id3.ID3(file_path)

    def _get_tag(self, tag_name: str = ...) -> str | None:
        tag = self.tags.get(tag_name)
        if tag:
            return tag.text[0]
        return None

    @property
    def title(self):
        return self._get_tag(tag_name=AudioTags._TITLE_TAG)

    @title.setter
    def title(self, value: str):
        self.tags.delall(AudioTags._TITLE_TAG)
        self.tags.add(mutagen.id3.TIT2(text=[value]))
        self.tags.save()

    @property
    def artist(self):
        return self._get_tag(tag_name=AudioTags._ARTIST_TAG)

    @artist.setter
    def artist(self, value: str):
        self.tags.delall(AudioTags._ARTIST_TAG)
        self.tags.add(mutagen.id3.TPE1(text=value))
        self.tags.save()

    @property
    def album(self):
        return self._get_tag(tag_name=AudioTags._ALBUM_TAG)

    @album.setter
    def album(self, value: str):
        self.tags.delall(AudioTags._ALBUM_TAG)
        self.tags.add(mutagen.id3.TALB(text=value))
        self.tags.save()

    @property
    def grouping(self):
        return self._get_tag(tag_name=AudioTags._GROUPING_TAG)

    @grouping.setter
    def grouping(self, value: str):
        self.tags.delall(AudioTags._GROUPING_TAG)
        self.tags.add(mutagen.id3.TIT1(text=value))
        self.tags.save()

    @property
    def artwork(self):
        for tag_name in self.tags.keys():
            if re.match(AudioTags._ARTWORK_TAG, tag_name):
                tag = self.tags.get(tag_name)
                return tag

    def set_artwork(self, data: bytes, mime_type: str):
        self.tags.delall(AudioTags._ARTWORK_TAG)
        self.tags.add(mutagen.id3.APIC(mime=mime_type, data=data))
        self.tags.save()

    def get_artwork_as_base64(self):
        tag = self.artwork
        if tag:
            buffer = io.BytesIO(tag.data)
            base64_string = base64.b64encode(buffer.getvalue()).decode()
            mime_type = tag.mime
            if not mime_type:
                if base64_string.startswith("/9j"):
                    mime_type = "image/jpg"
                elif base64_string.startswith("iVBORw0KGgo"):
                    mime_type = "image/png"
            return f"data:{mime_type};base64,{base64_string}"
        return None

    @classmethod
    def read_tags(cls, file_path: str):
        return AudioTags(file_path=file_path)


async def read_tags(file: bytes, filename: str):
    TAGS_DIRECTORY = "tags"

    tags_directory_path = await tempfiles.create_new_directory(
        directory=TAGS_DIRECTORY, raise_on_exists=False
    )
    directory_id = str(uuid.uuid4())
    directory_path = Path(tags_directory_path).joinpath(directory_id)
    await aiofiles.os.mkdir(directory_path)
    file_path = Path(directory_path).joinpath(filename)
    tags = TagsResponse()
    try:
        async with aiofiles.open(file_path, mode="wb") as f:
            await f.write(file)
        audio_tags = await asyncio.to_thread(AudioTags.read_tags, file_path)
        tags = TagsResponse(
            title=audio_tags.title,
            artist=audio_tags.artist,
            album=audio_tags.album,
            grouping=audio_tags.grouping,
            artwork_url=audio_tags.get_artwork_as_base64(),
        )
    except Exception:
        logger.exception(traceback.format_exc())
    finally:
        await asyncio.to_thread(shutil.rmtree, directory_path)

    return tags
