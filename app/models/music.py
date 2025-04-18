from app.models import Response


class GroupingResponse(Response):
    grouping: str


class ResolvedArtworkResponse(Response):
    resolved_artwork_url: str
