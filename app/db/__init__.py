from pathlib import Path

from litestar.plugins.sqlalchemy import (
    AlembicAsyncConfig,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.settings import settings

session_config = AsyncSessionConfig(expire_on_commit=False)
sqlalchemy_config = SQLAlchemyAsyncConfig(
    create_engine_callable=lambda name: create_async_engine(
        settings.async_database_url, poolclass=NullPool
    ),
    connection_string=settings.async_database_url,
    session_config=session_config,
    alembic_config=AlembicAsyncConfig(
        script_config=Path("app/db/alembic.ini"),
        script_location=Path("app/db/migrations"),
    ),
)
