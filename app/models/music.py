from typing import Literal, Optional

from pydantic import Field

from app.models import Response


class GroupingResponse(Response):
    grouping: str


class ResolvedArtworkResponse(Response):
    resolved_artwork_url: str


class MusicJobUpdateResponse(Response):
    id: str
    status: Literal["STARTED", "COMPLETED"]


class TagsResponse(Response):
    title: Optional[str] = Field(None)
    artist: Optional[str] = Field(None)
    album: Optional[str] = Field(None)
    grouping: Optional[str] = Field(None)
    artwork_url: Optional[str] = Field(None)
