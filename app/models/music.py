from pydantic import BaseModel


class GroupingResponse(BaseModel):
    grouping: str
