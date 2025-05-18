from typing import Literal, Optional

from litestar.datastructures import UploadFile
from pydantic import BaseModel, ConfigDict, HttpUrl

from app.models import Response


class GroupingResponse(Response):
    grouping: str


class ResolvedArtworkResponse(Response):
    resolved_artwork_url: str


class MusicJobUpdateResponse(Response):
    id: str
    status: Literal["STARTED", "COMPLETED"]


class TagsResponse(Response):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    grouping: Optional[str] = None
    artwork_url: Optional[str] = None


class CreateMusicJob(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file: Optional[UploadFile] = None
    video_url: Optional[HttpUrl] = None
    artwork_url: Optional[str] = None
    title: str
    artist: str
    album: str
    grouping: Optional[str] = None
