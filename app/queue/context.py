from redis.asyncio import Redis
from saq.types import Context
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker


class SAQContext(Context):
    db_engine: AsyncEngine
    db_sessionmaker: async_sessionmaker
    redis: Redis
