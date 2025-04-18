import logging
import traceback

from litestar import Router, get, status_codes
from litestar.exceptions import (
    ClientException,
)

from app.clients import google, ytdlp
from app.models.music import GroupingResponse
from app.utils import parse_youtube_video_id

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


router = Router(path="/music", route_handlers=[get_grouping], tags=["Music"])
