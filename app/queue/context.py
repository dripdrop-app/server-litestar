from saq.types import Context
from sqlalchemy.ext.asyncio import AsyncEngine


class SAQContext(Context):
    db_engine: AsyncEngine
