import asyncio
import logging
import shutil
import traceback
import uuid
from pathlib import Path

import aiofiles
import aiofiles.os

from app.clients.audiotags import AudioTags
from app.models.music import TagsResponse
from app.services import tempfiles

logger = logging.getLogger(__name__)


async def read_tags(file: bytes, filename: str):
    TAGS_DIRECTORY = "tags"

    tags_directory_path = await tempfiles.create_new_directory(directory=TAGS_DIRECTORY)
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
