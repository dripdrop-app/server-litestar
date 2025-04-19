import logging
import traceback
from typing import Annotated

from litestar import Router, get, post, status_codes
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import (
    ClientException,
)
from litestar.params import Body

from app.clients import audiotags, google, imagedownloader, ytdlp
from app.models.music import GroupingResponse, ResolvedArtworkResponse, TagsResponse
from app.utils.youtube import parse_youtube_video_id

logger = logging.getLogger(__name__)


@get("/grouping", status_code=status_codes.HTTP_200_OK, raises=[ClientException])
async def get_grouping(video_url: str) -> GroupingResponse:
    try:
        if "youtube.com" in video_url:
            video_id = parse_youtube_video_id(video_url)
            uploader = await google.get_video_uploader(video_id=video_id)
        else:
            video_info = await ytdlp.extract_video_info(url=video_url)
            uploader = video_info.get("uploader")
        return GroupingResponse(grouping=uploader)
    except Exception:
        logger.exception(traceback.format_exc())
        raise ClientException(detail="Unable to get grouping.")


@get("/artwork", status_code=status_codes.HTTP_200_OK, raises=[ClientException])
async def get_artwork(artwork_url: str) -> ResolvedArtworkResponse:
    try:
        resolved_artwork_url = await imagedownloader.resolve_artwork(
            artwork=artwork_url
        )
        return ResolvedArtworkResponse(resolved_artwork_url=resolved_artwork_url)
    except Exception:
        logger.exception(traceback.format_exc())
        raise ClientException(
            status_code=status_codes.HTTP_400_BAD_REQUEST,
            detail="Unable to get artwork.",
        )


@post("/tags", status_code=status_codes.HTTP_200_OK, raises=[ClientException])
async def get_tags(
    file: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
) -> TagsResponse:
    return await audiotags.read_tags(file=await file.read(), filename=file.filename)


router = Router(
    path="/music", route_handlers=[get_grouping, get_artwork, get_tags], tags=["Music"]
)
